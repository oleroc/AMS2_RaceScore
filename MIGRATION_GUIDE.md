# AMS2 RaceScore v1.7.0 Migration Guide

## Overview

Version 1.7.0 introduces a streamlined architecture with **separate migration utility** to reduce the main application size by ~1500 lines of code.

## Migration Architecture Changes

### Before v1.7.0
- **6183 lines** of code in main application
- 1500+ lines of migration code embedded in main app
- Migration executed automatically during startup
- Complex error handling within main application thread

### After v1.7.0 Refactor
- **5551 lines** of code in main application (**632 lines removed!**)
- **626 lines** in separate migration utility
- Clean separation of concerns
- Migration runs independently before application startup

## Migration Process

### For New Installations
1. Run `RaceMonitor_v1.7.0.py` directly
2. Application creates new v1.7.0 database automatically
3. No migration needed

### For Existing Databases (v1.5.0 or v1.6.0)

#### Option 1: Simple Batch File
```batch
Run_Database_Migration.bat
```

#### Option 2: Command Line
```bash
python migrate_to_v1_7_0.py
```

#### Option 3: Specific Database File
```bash
python migrate_to_v1_7_0.py path/to/your/database.db
```

## Migration Features

### Automatic Detection
- Detects v1.5.0, v1.6.0, or v1.7.0 databases
- Skips migration if already v1.7.0
- Comprehensive pre-migration analysis

### Safety Features
- **Automatic backup creation** before migration
- **Rollback capability** if migration fails
- **Data integrity verification** post-migration
- **Foreign key constraint validation**

### Performance Enhancements
- **10 performance indexes** created automatically
- **Foreign key relationships** properly established
- **Database size optimization** with VACUUM operations

## Migration Log

The utility creates `migration.log` with detailed information:
- Schema analysis before/after
- Data migration progress
- Error details if any issues occur
- Performance optimization results

## Main Application Changes

### Streamlined Database Class
```python
def check_and_migrate_database(self):
    """Check database version and suggest migration if needed"""
    # Detects legacy databases
    # Shows migration required dialog
    # Exits gracefully if migration needed
```

### Simplified Startup
- Fast startup (no migration processing)
- Clear error messages if migration required
- Automatic detection of database compatibility

## Benefits

1. **Reduced Memory Footprint**: 632 lines less code loaded at runtime
2. **Faster Startup**: No migration logic processing during startup
3. **Better Error Handling**: Migration errors don't crash main application
4. **Easier Maintenance**: Migration logic isolated and testable
5. **User-Friendly**: Clear instructions and automatic backup creation

## Troubleshooting

### If Migration Fails
1. Check `migration.log` for detailed error information
2. Restore from automatic backup: `RaceDB.db.backup_[timestamp]`
3. Report issues with log file for debugging

### If Application Won't Start
1. Run migration utility manually
2. Check database file permissions
3. Ensure Python 3.7+ is installed
4. Verify all files are in same directory

## File Structure

```
AMS2_RaceScore/
├── RaceMonitor_v1.7.0.py          # Main application (5551 lines)
├── migrate_to_v1_7_0.py            # Migration utility (626 lines)
├── Run_Database_Migration.bat      # User-friendly migration runner
├── RaceDB.db                       # Database file
├── migration.log                   # Migration log (created during migration)
└── RaceDB.db.backup_*              # Automatic backups
```

## Technical Details

### Tables Added in v1.7.0
- **Sessions**: Multi-race session management
- **SessionParticipants**: 50% participant matching for session assignment
- **DatabaseMetadata**: Version tracking and metadata

### Enhanced Tables
- **Races**: Added SessionID, IsCompleted, CompletedAt, IPAddress columns
- **All tables**: Proper foreign key constraints established

### Performance Indexes
- `idx_races_session`, `idx_races_date`, `idx_races_completed`
- `idx_sessions_completed`, `idx_session_participants`
- `idx_participants_race`, `idx_laps_race`, `idx_laps_name`
- And more for optimal query performance

## Version History

- **v1.5.0**: Basic single-race monitoring
- **v1.6.0**: Added SessionID column
- **v1.7.0**: Multi-race monitoring with separated migration utility

---

*This migration system ensures smooth upgrades while keeping the main application lean and efficient.*
