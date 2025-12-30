## Improved authentication logging and reduced warning verbosity

### Changes Made:
- **Suppressed bcrypt initialization warnings** by temporarily raising log level during context creation
- **Reduced authentication failure log verbosity** from WARNING to DEBUG level
- **Improved password length handling** with proper byte counting and truncation
- **Enhanced error handling** for bcrypt compatibility issues

### Technical Details:
- Authentication failures now log at DEBUG level instead of WARNING to reduce log noise
- Added proper password byte length checking before bcrypt operations
- Suppressed passlib bcrypt handler warnings during initialization
- Maintained security while improving log cleanliness

### Impact:
- **Cleaner logs**: Failed login attempts no longer generate multiple warning messages
- **Better debugging**: Important auth errors still logged, but routine failures are less verbose
- **Reduced log noise**: Bcrypt compatibility warnings suppressed during normal operation
- **Maintained security**: All authentication checks still function correctly
