# Guide to Delete Users from PostgreSQL Database

## ⚠️ IMPORTANT: Backup First!

Before deleting any records, always backup your database:

```sql
-- Create a backup (run in terminal/command prompt)
pg_dump -U your_username -d your_database_name -f backup.sql
```

## Method 1: Using pgAdmin Query Tool (Recommended)

### Step 1: Open Query Tool
1. Open pgAdmin
2. Connect to your PostgreSQL server
3. Navigate to: **Servers** → **Your Server** → **Databases** → **lifepath** (or your DB name) → **Schemas** → **public**
4. Right-click on **lifepath** database → **Query Tool**

### Step 2: Delete Chart Data First (if exists)
Since `chart_data` table references `users` table, delete chart data first:

```sql
-- Delete all chart data
DELETE FROM chart_data;

-- Or delete chart data for specific user
DELETE FROM chart_data WHERE user_id = 1;
```

### Step 3: Delete Users

**Option A: Delete Specific User**
```sql
-- Delete by email
DELETE FROM users WHERE email = 'user@example.com';

-- Delete by ID
DELETE FROM users WHERE id = 1;
```

**Option B: Delete Multiple Users**
```sql
-- Delete users by email list
DELETE FROM users WHERE email IN ('user1@example.com', 'user2@example.com');

-- Delete users by date (older than specific date)
DELETE FROM users WHERE created_at < '2024-01-01';
```

**Option C: Delete All Users**
```sql
-- WARNING: This deletes ALL users
DELETE FROM users;
```

### Step 4: Verify Deletion
```sql
-- Check remaining users
SELECT COUNT(*) FROM users;

-- View all users
SELECT id, email, name, created_at FROM users;
```

## Method 2: Using pgAdmin GUI (View Data)

1. Navigate to **Tables** → **users**
2. Right-click **users** → **View/Edit Data** → **All Rows**
3. Select the row(s) you want to delete (use Ctrl+Click for multiple)
4. Press **Delete** key or right-click → **Delete Row**
5. Click **Yes** to confirm

## Method 3: Using psql Command Line

```bash
# Connect to database
psql -U your_username -d your_database_name

# Then run SQL commands
DELETE FROM chart_data;
DELETE FROM users WHERE email = 'user@example.com';
```

## Safety Tips

1. **Always backup first** before deleting data
2. **Test on a single record** before bulk deletion
3. **Check foreign key constraints** - delete related records first
4. **Use transactions** to rollback if needed:

```sql
-- Start transaction
BEGIN;

-- Delete operations
DELETE FROM chart_data WHERE user_id = 1;
DELETE FROM users WHERE id = 1;

-- Review the results, then either:
COMMIT;  -- Save changes
-- OR
ROLLBACK; -- Undo changes
```

## Foreign Key Relationship

Your database has:
- `users` table (parent)
- `chart_data` table (child) with `user_id` referencing `users.id`

**To delete users, you must:**
1. Delete from `chart_data` first, OR
2. Set up CASCADE delete (automatically deletes related records)

## Setting Up CASCADE Delete (Optional)

If you want to automatically delete chart_data when a user is deleted, you would need to modify the model:

```python
# In models.py - ChartData class
user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
```

Then recreate the table or use a migration.


