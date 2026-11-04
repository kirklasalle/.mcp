# 🔄 VS Code Restart Instructions for VRGC MCP Server

**Created:** October-15-2024  
**Updated:** August-04-2025  
**Author:** Virtually Robotic GitHub Copilot  
**Tags:** #vrgc/restart_guide.md #documentation #gpu_optimization #testing #training  
**Category:** Documentation  
**Status:** Superseded by current project-local MCP verification.

> This guide's setup, dependency, and five-tool claims are a 2025 snapshot and
> do not describe the current SpaceEntropyCompression profile. The current
> VRGC catalog contains ten tools: `vrgc_self_heal_code`, `vrgc_web_fetch`,
> `vrgc_web_search`, `vrgc_download_file`, `vrgc_ftp_access`,
> `vrgc_api_request`, `vrgc_assess_system`, `vrgc_monitor_training`,
> `vrgc_optimize_hardware`, and `vrgc_verify_covenant`.
> `vrgc_analyze_intelligence` is not currently advertised. Download, FTP, and
> API-request calls require per-call approval and the mutation opt-in. See the
> project-local MCP verification in `../README.md`.

The current local protocol gate verifies VRGC initialization, tool schemas,
three read-only operations, and denial of download/FTP calls without explicit
approval. This is not a functional certification of all ten tools.

### Restart Steps
1. **Save all work** (if needed)
2. **Close VS Code completely** (File → Exit or Alt+F4)
3. **Wait 5 seconds** for complete shutdown
4. **Reopen VS Code** in ImpressionCore project folder
5. **Wait for MCP initialization** (check VS Code status bar)

### After Restart - Test MCP Integration
The following VRGC tools should be available through MCP:

- `vrgc_assess_system` - System assessment and hardware analysis
- `vrgc_monitor_training` - B1 training progress monitoring  
- `vrgc_optimize_hardware` - GTX 1050 Ti optimization
- `vrgc_verify_covenant` - Sacred Covenant file integrity
- `vrgc_analyze_intelligence` - Project intelligence and code analysis

### Quick Test Commands
```
@impressioncore-vrgc vrgc_assess_system
@impressioncore-vrgc vrgc_analyze_intelligence --analyze
```

### Troubleshooting
If VRGC MCP server doesn't load:
1. Check VS Code output panel for MCP errors
2. Verify Python path in `.vscode/mcp.json` is correct
3. Ensure `.venv310` environment is accessible
4. Check VRGC debug logs in VS Code developer tools

**Status**: Ready for restart - VRGC implementation complete! 🚀
