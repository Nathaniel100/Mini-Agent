# Mini-Agent 流程图

## 1. 主程序启动流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Main Entry Flow                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  mini-agent CLI (cli.py:main)                                               │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────┐                                                     │
│  │ parse_args()       │  解析命令行参数                                      │
│  │ --workspace, --task │                                                     │
│  └──────────┬──────────┘                                                     │
│             │                                                                │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ run_agent()         │  异步入口函数                                       │
│  └──────────┬──────────┘                                                     │
│             │                                                                │
│             ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                     Initialization Phase                           │     │
│  │                                                                    │     │
│  │  1. Config.load()                                                │     │
│  │     ├── Find config.yaml (priority: dev > user > package)       │     │
│  │     ├── Parse YAML                                               │     │
│  │     └── Return Config object                                     │     │
│  │                                                                    │     │
│  │  2. LLMClient.__init__()                                         │     │
│  │     ├── Create retry config                                      │     │
│  │     ├── Detect provider (anthropic/openai)                       │     │
│  │     └── Instantiate appropriate client                           │     │
│  │                                                                    │     │
│  │  3. initialize_base_tools()                                       │     │
│  │     ├── BashOutputTool, BashKillTool (auxiliary)                 │     │
│  │     ├── SkillLoader + create_skill_tools()                       │     │
│  │     │   └── Discover SKILL.md files                              │     │
│  │     └── load_mcp_tools_async()                                    │     │
│  │         └── Connect to MCP servers                                │     │
│  │                                                                    │     │
│  │  4. add_workspace_tools()                                        │     │
│  │     ├── BashTool (with workspace as cwd)                         │     │
│  │     ├── ReadTool, WriteTool, EditTool                            │     │
│  │     └── SessionNoteTool                                          │     │
│  │                                                                    │     │
│  │  5. Load System Prompt                                           │     │
│  │     └── Inject Skills Metadata (Progressive Disclosure)          │     │
│  │                                                                    │     │
│  │  6. Create Agent instance                                        │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│             │                                                                │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ Interactive Mode    │  非交互模式: run_agent(task)                        │
│  │ (Prompt Session)    │  交互模式: 启动 prompt_toolkit 会话                 │
│  └──────────┬──────────┘                                                     │
│             │                                                                │
│             ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                     Message Loop                                  │     │
│  │                                                                    │     │
│  │  while True:                                                      │     │
│  │    user_input = await session.prompt_async()                    │     │
│  │                                                                    │     │
│  │    if user_input.startswith("/"):                                │     │
│  │        # Handle commands: /help, /clear, /stats, /log, /exit     │     │
│  │    else:                                                          │     │
│  │        agent.add_user_message(user_input)                        │     │
│  │        await agent.run()  # Execute agent loop                  │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│             │                                                                │
│             ▼                                                                │
│  ┌─────────────────────┐                                                     │
│  │ Cleanup            │                                                     │
│  │ cleanup_mcp_       │                                                     │
│  │   connections()    │                                                     │
│  └─────────────────────┘                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Agent 核心执行循环

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Agent Run Loop (agent.py)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  async def agent.run(cancel_event=None)                                      │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    STEP LOOP (max_steps)                           │   │
│  │                                                                    │   │
│  │  step = 0                                                          │   │
│  │  while step < max_steps:                                          │   │
│  │      │                                                             │   │
│  │      ▼                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ 1. Check Cancellation                                        │ │   │
│  │  │    if cancel_event.is_set():                                │ │   │
│  │  │       cleanup_incomplete_messages()                          │ │   │
│  │  │       return "Task cancelled"                                │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │      │                                                             │   │
│  │      ▼                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ 2. Check & Summarize Messages                               │ │   │
│  │  │    await _summarize_messages()                              │ │   │
│  │  │    - Estimate token count with tiktoken                     │ │   │
│  │  │    - If exceeds token_limit (80000):                        │ │   │
│  │  │      * Summarize execution between user messages            │ │   │
│  │  │      * Replace with summary                                 │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │      │                                                             │   │
│  │      ▼                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ 3. Log Request                                               │ │   │
│  │  │    logger.log_request(messages, tools)                      │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │      │                                                             │   │
│  │      ▼                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ 4. Call LLM                                                  │ │   │
│  │  │    response = await llm.generate(                           │ │   │
│  │  │        messages=self.messages,                              │ │   │
│  │  │        tools=tool_list                                      │ │   │
│  │  │    )                                                         │ │   │
│  │  │    - Includes retry with exponential backoff               │ │   │
│  │  │    - Returns: content, thinking, tool_calls, usage          │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │      │                                                             │   │
│  │      ▼                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ 5. Log Response                                              │ │   │
│  │  │    logger.log_response(response)                            │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │      │                                                             │   │
│  │      ▼                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ 6. Add Assistant Message                                     │ │   │
│  │  │    messages.append(Message(role="assistant", ...))          │ │   │
│  │  │    - content, thinking, tool_calls                           │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │      │                                                             │   │
│  │      ▼                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ 7. Check if Complete                                         │ │   │
│  │  │    if not response.tool_calls:                              │ │   │
│  │  │       return response.content  # Task complete!            │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │      │                                                             │   │
│  │      ▼                                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ 8. Execute Tool Calls                                        │ │   │
│  │  │    for tool_call in response.tool_calls:                    │ │   │
│  │  │        │                                                     │ │   │
│  │  │        ▼                                                     │ │   │
│  │  │    ┌────────────────────────────────────────────────────┐  │ │   │
│  │  │    │ a. Check Cancellation                                │  │ │   │
│  │  │    │    if cancel_event.is_set(): break                 │  │ │   │
│  │  │    └────────────────────────────────────────────────────┘  │ │   │
│  │  │        │                                                     │ │   │
│  │  │        ▼                                                     │ │   │
│  │  │    ┌────────────────────────────────────────────────────┐  │ │   │
│  │  │    │ b. Execute Tool                                      │  │ │   │
│  │  │    │    tool = tools[function_name]                       │  │ │   │
│  │  │    │    result = await tool.execute(**arguments)         │  │ │   │
│  │  │    └────────────────────────────────────────────────────┘  │ │   │
│  │  │        │                                                     │ │   │
│  │  │        ▼                                                     │ │   │
│  │  │    ┌────────────────────────────────────────────────────┐  │ │   │
│  │  │    │ c. Log Tool Result                                   │  │ │   │
│  │  │    │    logger.log_tool_result(result)                    │  │ │   │
│  │  │    └────────────────────────────────────────────────────┘  │ │   │
│  │  │        │                                                     │ │   │
│  │  │        ▼                                                     │ │   │
│  │  │    ┌────────────────────────────────────────────────────┐  │ │   │
│  │  │    │ d. Add Tool Message to History                       │  │ │   │
│  │  │    │    messages.append(Message(role="tool", ...))      │  │ │   │
│  │  │    └────────────────────────────────────────────────────┘  │ │   │
│  │  │        │                                                     │ │   │
│  │  │        ▼                                                     │ │   │
│  │  │    ┌────────────────────────────────────────────────────┐  │ │   │
│  │  │    │ e. Check Cancellation (post-tool)                   │  │ │   │
│  │  │    │    if cancel_event.is_set(): break                  │  │ │   │
│  │  │    └────────────────────────────────────────────────────┘  │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │      │                                                             │   │
│  │      ▼                                                             │   │
│  │  step += 1                                                         │   │
│  │                                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────┐                                                   │
│  │ Max Steps Reached   │                                                    │
│  │ return "Task        │                                                    │
│  │ couldn't be        │                                                    │
│  │ completed after    │                                                    │
│  │ N steps."          │                                                    │
│  └─────────────────────┘                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. 工具初始化顺序

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Tool Initialization Order                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  async def initialize_base_tools(config)                                      │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 1: Bash Auxiliary Tools                                        │   │
│  │                                                                      │   │
│  │  BashOutputTool  ──┐                                                │   │
│  │                     │   (Independent of workspace)                  │   │
│  │  BashKillTool   ───┘                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 2: Skill Tools (if enabled)                                    │   │
│  │                                                                      │   │
│  │  SkillLoader                                                        │   │
│  │      │                                                              │   │
│  │      ▼                                                              │   │
│  │  discover_skills() ─────────────────────────────────────┐          │   │
│  │                                                      │              │   │
│  │  For each SKILL.md:                                  │              │   │
│  │    ├── Parse YAML frontmatter                        │              │   │
│  │    ├── Extract name, description                     │              │   │
│  │    ├── Process relative paths → absolute            │              │   │
│  │    └── Create Skill object                          │              │   │
│  │                                                      │              │   │
│  │  create_skill_tools()                               │              │   │
│  │    └── Return SkillTool (get_skill function)        │              │   │
│  └──────────────────────────────────────────────────────┘              │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 3: MCP Tools (if enabled)                                      │   │
│  │                                                                      │   │
│  │  load_mcp_tools_async(config_path)                                 │   │
│  │      │                                                              │   │
│  │      ▼                                                              │   │
│  │  For each MCP server in mcp.json:                                  │   │
│  │      │                                                              │   │
│  │      ▼                                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │ MCPServerConnection.connect()                               │  │   │
│  │  │      │                                                       │  │   │
│  │  │      ▼                                                       │  │   │
│  │  │  Determine connection type:                                  │  │   │
│  │  │    ├── "stdio"  → stdio_client                              │  │   │
│  │  │    ├── "sse"    → sse_client                                │  │   │
│  │  │    └── "streamable_http" → streamablehttp_client          │  │   │
│  │  │                                                           │  │   │
│  │  │  Create ClientSession                                       │  │   │
│  │  │  session.initialize()                                       │  │   │
│  │  │  session.list_tools()                                       │  │   │
│  │  │                                                           │  │   │
│  │  │  For each tool:                                            │  │   │
│  │  │    Wrap as MCPTool with timeout                            │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  def add_workspace_tools(tools, config, workspace_dir)                        │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 4: Workspace-Dependent Tools                                   │   │
│  │                                                                      │   │
│  │  BashTool(workspace_dir as cwd)                                     │   │
│  │                                                                      │   │
│  │  ReadTool(workspace_dir) ──┐                                         │   │
│  │  WriteTool(workspace_dir)  ├─ (Path resolution)                    │   │
│  │  EditTool(workspace_dir) ─┘                                         │   │
│  │                                                                      │   │
│  │  SessionNoteTool(memory_file)                                        │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4. LLM 调用流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LLM Call Flow                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  agent.llm.generate(messages, tools)                                         │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LLMClient.generate()                                                │   │
│  │      │                                                              │   │
│  │      ▼                                                              │   │
│  │  @async_retry decorator ─────────────────────────────────────┐     │   │
│  │                                                     │          │     │   │
│  │  For attempt in range(max_retries + 1):             │          │     │   │
│  │      │                                            │          │     │   │
│  │      ▼                                            │          │     │   │
│  │  ┌────────────────────────────────────────────┐    │          │     │   │
│  │  │ Retry Logic                               │    │          │     │   │
│  │  │                                           │    │          │     │   │
│  │  │ 1. Calculate delay:                       │    │          │     │   │
│  │  │      delay = initial_delay * (base ^     │    │          │     │   │
│  │  │                     attempt)              │    │          │     │   │
│  │  │                                           │    │          │     │   │
│  │  │ 2. Call retry callback (if set):          │    │          │     │   │
│  │  │      on_retry(exception, attempt)         │    │          │     │   │
│  │  │                                           │    │          │     │   │
│  │  │ 3. Sleep before retry:                    │    │          │     │   │
│  │  │      await asyncio.sleep(delay)          │    │          │     │   │
│  │  │                                           │    │          │     │   │
│  │  └────────────────────────────────────────────┘    │          │     │   │
│  │      │                                            │          │     │   │
│  │      ▼                                            │          │     │   │
│  │  ┌────────────────────────────────────────────┐    │          │     │   │
│  │  │ _client.generate()                         │    │          │     │   │
│  │  │                                            │    │          │     │   │
│  │  │ If provider == ANTHROPIC:                  │    │          │     │   │
│  │  │    AnthropicClient.generate()             │    │          │     │   │
│  │  │                                            │    │          │     │   │
│  │  │    1. Convert messages to Anthropic format│    │          │     │   │
│  │  │    2. Convert tools to Anthropic schema   │    │          │     │   │
│  │  │    3. POST /v1/messages                    │    │          │     │   │
│  │  │    4. Parse response:                      │    │          │     │   │
│  │  │       - content → text                    │    │          │     │   │
│  │  │       - thinking → thinking               │    │          │     │   │
│  │  │       - tool_calls → ToolCall[]           │    │          │     │   │
│  │  │       - usage → TokenUsage                │    │          │     │   │
│  │  │                                            │    │          │     │   │
│  │  │ If provider == OPENAI:                     │    │          │     │   │
│  │  │    OpenAIClient.generate()                │    │          │     │   │
│  │  │                                            │    │          │     │   │
│  │  │    1. Convert messages to OpenAI format   │    │          │     │   │
│  │  │    2. Convert tools to OpenAI schema      │    │          │     │   │
│  │  │    3. POST /v1/chat/completions           │    │          │     │   │
│  │  │    4. Parse response                      │    │          │     │   │
│  │  └────────────────────────────────────────────┘    │          │     │   │
│  │      │                                            │          │     │   │
│  │      ▼                                            │          │     │   │
│  │  Return LLMResponse ◄─────────────────────────────┘          │     │   │
│  │                                                                    │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5. 消息摘要流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Message Summarization Flow                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  async def _summarize_messages()                                            │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 1: Check if summarization is needed                           │   │
│  │                                                                      │   │
│  │  estimated_tokens = _estimate_tokens()                             │   │
│  │                                                                      │   │
│  │  should_summarize = (                                               │   │
│  │      estimated_tokens > token_limit      OR                       │   │
│  │      api_total_tokens > token_limit                                │   │
│  │  )                                                                  │   │
│  │                                                                      │   │
│  │  if not should_summarize: return  # Skip                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 2: Find user message indices                                  │   │
│  │                                                                      │   │
│  │  user_indices = [i for i, msg in enumerate(messages)              │   │
│  │                  if msg.role == "user" and i > 0]                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 3: Build new message list with summaries                     │   │
│  │                                                                      │   │
│  │  new_messages = [messages[0]]  # Keep system prompt               │   │
│  │                                                                      │   │
│  │  For each user message:                                            │   │
│  │      │                                                              │   │
│  │      ▼                                                              │   │
│  │  ┌────────────────────────────────────────────────────────────┐   │   │
│  │  │ a. Add user message                                        │   │   │
│  │  │    new_messages.append(messages[user_idx])                │   │   │
│  │  │                                                            │   │   │
│  │  │ b. Extract execution messages (between users)              │   │   │
│  │  │    execution_messages = messages[user_idx+1 : next_user]  │   │   │
│  │  │                                                            │   │   │
│  │  │ c. Summarize execution                                     │   │   │
│  │  │    if execution_messages:                                 │   │   │
│  │  │        summary = await _create_summary(                   │   │   │
│  │  │            execution_messages, round_num                  │   │   │
│  │  │        )                                                   │   │   │
│  │  │        new_messages.append(Message(                       │   │   │
│  │  │            role="user",                                    │   │   │
│  │  │            content=f"[Summary]\n{summary}"               │   │   │
│  │  │        ))                                                   │   │   │
│  │  └────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Step 4: Replace message list                                       │   │
│  │                                                                      │   │
│  │  self.messages = new_messages                                      │   │
│  │  _skip_next_token_check = True  # Avoid consecutive triggers      │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  async def _create_summary(messages, round_num)                             │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ LLM Summarization                                                   │   │
│  │                                                                      │   │
│  │  summary_prompt = """                                               │   │
│  │      Summarize the following Agent execution:                     │   │
│  │                                                                      │   │
│  │      {execution_content}                                          │   │
│  │                                                                      │   │
│  │      Requirements:                                                 │   │
│  │      - Focus on completed tasks and tool calls                    │   │
│  │      - Keep key results and findings                              │   │
│  │      - Within 1000 words                                           │   │
│  │  """                                                               │   │
│  │                                                                      │   │
│  │  response = await llm.generate([                                   │   │
│  │      Message(role="system", content="You are a summarizer."),     │   │
│  │      Message(role="user", content=summary_prompt)                 │   │
│  │  ])                                                                 │   │
│  │                                                                      │   │
│  │  return response.content                                           │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6. 交互式会话流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Interactive Session Flow                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  prompt_toolkit Session Loop                                                 │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ user_input = await session.prompt_async()                         │   │
│  │   - Displays "You › " prompt                                      │   │
│  │   - Supports multiline (Ctrl+J)                                   │   │
│  │   - History search (↑/↓)                                         │   │
│  │   - Auto-complete (Tab)                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Command Handling                                                   │   │
│  │                                                                      │   │
│  │  if user_input.startswith("/"):                                  │   │
│  │                                                                      │   │
│  │  /help    → print_help()                                          │   │
│  │  /clear   → agent.messages = [system_prompt]                     │   │
│  │  /history → print(len(agent.messages))                            │   │
│  │  /stats   → print_stats(agent, session_start)                     │   │
│  │  /log     → show_log_directory() / read_log_file()               │   │
│  │  /exit    → break loop, cleanup                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Execute Agent                                                       │   │
│  │                                                                      │   │
│  │  agent.add_user_message(user_input)                               │   │
│  │                                                                      │   │
│  │  # Create cancellation event                                       │   │
│  │  cancel_event = asyncio.Event()                                   │   │
│  │  agent.cancel_event = cancel_event                                 │   │
│  │                                                                      │   │
│  │  # Start Esc key listener (background thread)                    │   │
│  │  esc_thread = threading.Thread(target=esc_key_listener)           │   │
│  │  esc_thread.start()                                                │   │
│  │                                                                      │   │
│  │  # Run agent                                                        │   │
│  │  agent_task = asyncio.create_task(agent.run())                    │   │
│  │                                                                      │   │
│  │  # Poll for cancellation                                           │   │
│  │  while not agent_task.done():                                     │   │
│  │      if esc_cancelled[0]:                                         │   │
│  │          cancel_event.set()                                        │   │
│  │      await asyncio.sleep(0.1)                                     │   │
│  │                                                                      │   │
│  │  result = await agent_task                                         │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Print Result                                                        │   │
│  │                                                                      │   │
│  │  print(result)  # Agent's final response                         │   │
│  │  print_separator()                                                 │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         └──────────────┐                                                   │
│                        │                                                   │
│                        ▼                                                   │
│                 (Next iteration)                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```
