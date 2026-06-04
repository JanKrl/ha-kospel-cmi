# Home Assistant Integration Development Guidelines

This repository creates a Home Assistant integration. All development work should be guided by the official Home Assistant developer documentation.

## Official Documentation

**Always refer to the official Home Assistant developer documentation for authoritative guidance:**
- 📖 **Home Assistant Development Index**: https://developers.home-assistant.io/docs/development_index/

This documentation covers:
- Integration architecture and best practices
- Component lifecycle and entity management
- Configuration schemas and validation
- Async operations and coroutines
- Logging and debugging
- Testing patterns and fixtures
- API endpoints and state management

When uncertain about implementation patterns, API usage, or Home Assistant conventions, consult the official docs first.

## Integration Development

- Follow Home Assistant's async/await patterns as documented
- Use typing and follow the entity component model
- Implement proper discovery and configuration flows
- Write tests using Home Assistant's testing utilities

## Code Quality

- Use type hints throughout (required for Home Assistant integrations)
- Follow PEP 8 style conventions
- Include docstrings for public methods
- Add logging for debugging and troubleshooting
- Test both success and error scenarios

## References

- **Developer Documentation**: https://developers.home-assistant.io/docs/development_index/
- **Integration Architecture**: https://developers.home-assistant.io/docs/architecture_index/
- **Entity Component**: https://developers.home-assistant.io/docs/entity_index/
