# MCP Server Configuration

This project uses Model Context Protocol (MCP) servers to enhance agent capabilities with external tools and data sources.

## Configured MCP Servers

The project has 4 MCP servers configured in `.vscode/mcp.json`:

### 1. Context7 (Auto-fetch live documentation)

**Purpose**: Automatically fetches up-to-date documentation for any library before agents write code. Eliminates bugs from wrong API shapes, deprecated patterns, or version mismatches.

**Setup**:
1. Get API key from [Upstash Context7](https://upstash.com/docs/context7/overall/getstarted)
2. Open `.vscode/mcp.json`
3. Replace `YOUR_CONTEXT7_API_KEY_HERE` with your actual API key

**Usage**: Automatic - agents will fetch docs when working with libraries.

---

### 2. Playwright (Browser automation)

**Purpose**: Browser automation for screenshots, user-flow testing, responsive testing, and UI verification.

**Setup**: No configuration needed - works out of the box.

**Usage**:
- Run `npm run dev` to start the frontend
- Ask agents to test flows, capture screenshots, or verify responsive behavior
- Example: "Take a screenshot of the login page" or "Test the file upload flow"

---

### 3. Filesystem (Workspace access)

**Purpose**: High-speed workspace read/write access for bootstrap generation, scanning codebases, and batch file operations.

**Setup**: Already configured to point to project root. No changes needed.

**Usage**: Automatic - agents use this for file operations.

---

### 4. GitHub (Repository intelligence)

**Purpose**: Repository intelligence and GitHub workflow automation. Can search code, create issues, open PRs, review commits, and inspect repositories.

**Setup**:
1. Create a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `read:org`, `read:user`
   - Copy the token
2. Open `.vscode/mcp.json`
3. Replace `YOUR_GITHUB_TOKEN_HERE` with your token

**Usage**:
- "Create an issue for this bug"
- "Open a PR with these changes"
- "Search for similar implementations in the repo"

---

## Verifying MCP Server Status

In VS Code with GitHub Copilot or Claude Code:
1. Open the command palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Search for "MCP" or check the status bar
3. Verify all 4 servers show as "Connected"

If a server fails to connect:
- Check that API keys are correctly set in `.vscode/mcp.json`
- Ensure you have Node.js 18+ installed
- Try restarting VS Code

---

## Optional: Additional MCP Servers

You can add more MCP servers based on your needs. Popular options:

- **Sequential Thinking**: Enhanced reasoning for complex problems
- **Chrome DevTools**: Deep browser debugging via Chrome DevTools Protocol
- **MarkItDown**: Convert documents (PDF, DOCX, etc.) to markdown

See [MCP Server Registry](https://github.com/modelcontextprotocol/servers) for more options.

To add a server, edit `.vscode/mcp.json` and add a new entry under `"servers"`.
