# FastMCP

## Overview

FastMCP is a Pythonic framework for building MCP (Model Context Protocol) servers and clients. It provides a fast, well-typed interface for connecting AI applications with external tools, resources, and services.

## Features

### Core Functionality

- **MCP Server Implementation**: Build MCP servers with tools, resources, and prompts
- **MCP Client Implementation**: Programmatic client for interacting with MCP servers
- **Tool Operations**: Discover and execute server-side tools
- **Resource Operations**: Access static and templated resources from MCP servers
- **Prompt Management**: Use server-side prompt templates with automatic argument serialization
- **User Elicitation**: Handle server-initiated user input requests with structured schemas
- **LLM Sampling**: Handle server-initiated LLM sampling requests
- **Progress Monitoring**: Handle progress notifications from long-running server operations
- **Message Handling**: Handle MCP messages, requests, and notifications with custom handlers
- **Server Logging**: Receive and handle log messages from MCP servers

### Authentication & Security

- **Bearer Token Authentication**: Authenticate clients with Bearer tokens
- **OAuth 2.1 Authentication**: Full OAuth integration support
- **Multiple OAuth Providers**: Support for Auth0, AWS Cognito, Azure (Microsoft Entra ID), Discord, GitHub, Google, OCI IAM, and others
- **JWT Token Verification**: Validate tokens issued by external systems
- **Policy-based Authorization**: Integration with Eunomia and Permit.io for fine-grained authorization

### Deployment & Configuration

- **Multiple Deployment Options**: HTTP deployment, FastMCP Cloud, local development
- **Project Configuration**: Portable, declarative configuration via fastmcp.json
- **Storage Backends**: Persistent and distributed storage for caching and OAuth state
- **Server Composition**: Combine multiple FastMCP servers into larger applications

### Advanced Capabilities

- **Background Tasks**: Execute operations asynchronously with progress tracking
- **Server Proxy Functionality**: Act as an intermediary for other MCP servers
- **Middleware Support**: Add cross-cutting functionality with request/response processing
- **Template System**: Dynamic content generation with templates
- **Event Store**: Maintain state and events within the server

## Architecture

### Server Architecture

- Core server class for building MCP applications
- Support for tools, resources, and prompts
- Context system for accessing MCP capabilities
- Middleware for cross-cutting concerns
- OpenAPI integration for routing and components
- Low-level protocol handling

### Client Architecture

- Well-typed, Pythonic interface
- Multiple transport options for server communication
- Message handling and progress tracking
- Authentication support (Bearer, OAuth)
- Resource and tool access

### Integration Architecture

- Support for multiple LLM providers (Anthropic, OpenAI, Google Gemini, ChatGPT)
- IDE integrations (Cursor, Claude Code, Claude Desktop)
- Third-party service integrations (Auth0, Supabase, WorkOS, etc.)

## Usage

### Getting Started

- Installation and quickstart guides available
- Command-line interface (CLI) for common operations
- Local server running for development and testing

### Development Patterns

- Decorator patterns for method handling
- Testing frameworks for server validation
- Tool transformation for enhanced variants
- Contrib modules for community extensions

### Configuration

- Declarative configuration via fastmcp.json
- Environment-specific configurations
- Filesystem-based configuration sources

## Integration Capabilities

### LLM Integrations

- Anthropic API integration
- OpenAI API integration
- Google Gemini SDK integration
- ChatGPT integration (Chat and Deep Research modes)
- Claude Code and Claude Desktop support

### IDE Integrations

- Cursor IDE support
- Claude Code integration
- Claude Desktop integration
- Gemini CLI installation

### Authentication Integrations

- Auth0 OAuth
- AWS Cognito OAuth
- Azure (Microsoft Entra ID) OAuth
- Discord OAuth
- GitHub OAuth
- Google OAuth
- OCI IAM OAuth
- Supabase Auth
- WorkOS Connect
- Descope integration
- Scalekit support

### Framework Integrations

- FastAPI integration
- OpenAPI specification support
- Standard MCP configuration file generation

### Other Integrations

- Eunomia policy-based authorization
- Permit.io fine-grained authorization
- MCP JSON configuration support

## Development & Maintenance

### Development Process

- Contributing guidelines for developers
- Testing patterns and requirements
- Versioning and release process
- Upgrade guides for version migrations

### CLI Tools

- Command-line interface for server management
- Installation tools for various platforms
- Configuration and deployment utilities
