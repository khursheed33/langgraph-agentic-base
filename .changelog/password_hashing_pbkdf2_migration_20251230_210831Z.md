## Migrated password hashing from bcrypt to pbkdf2_sha256

### Changes Made:
- **Switched primary password hashing scheme** from bcrypt to pbkdf2_sha256
- **Removed bcrypt version compatibility issues** that were causing login failures
- **Eliminated password length restrictions** (bcrypt's 72-byte limit)
- **Maintained backward compatibility** with existing bcrypt hashes

### Technical Details:
- **New scheme**: `pbkdf2_sha256` with 30,000 rounds for strong security
- **Fallback support**: Still supports verifying existing bcrypt hashes
- **No length limits**: pbkdf2 handles passwords of any reasonable length
- **Better compatibility**: No version detection issues with pbkdf2

### Security Impact:
- **Maintained strength**: pbkdf2_sha256 with 30k rounds is cryptographically strong
- **Future-proof**: No dependency on problematic bcrypt library versions
- **Compatible**: Existing user accounts continue to work seamlessly

### Migration:
- **Automatic**: New passwords use pbkdf2_sha256
- **Transparent**: Existing bcrypt hashes still verify correctly
- **Hash upgrades**: Old bcrypt hashes automatically upgrade to pbkdf2 on successful login
- **No user action required**: Login works for all existing accounts
