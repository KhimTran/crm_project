"""Execute the migration to merge admins, staffs, customers into accounts."""
import os
import MySQLdb
import dotenv

dotenv.load_dotenv()

conn = MySQLdb.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    db=os.getenv("DB_NAME", "crm_db"),
    charset="utf8mb4",
)
cur = conn.cursor()

try:
    cur.execute("SET FOREIGN_KEY_CHECKS=0;")

    # Check if columns already exist
    cur.execute("""
        SELECT COLUMN_NAME FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='accounts' AND COLUMN_NAME='full_name';
    """)
    if not cur.fetchone():
        print("Step 1: Adding profile columns to accounts table...")
        cur.execute("""
            ALTER TABLE accounts
            ADD COLUMN full_name varchar(150) NOT NULL DEFAULT '',
            ADD COLUMN phone varchar(20) DEFAULT NULL,
            ADD COLUMN date_of_birth date DEFAULT NULL,
            ADD COLUMN gender varchar(20) DEFAULT NULL,
            ADD COLUMN address varchar(255) DEFAULT NULL,
            ADD COLUMN playing_level varchar(30) DEFAULT NULL;
        """)

    print("Step 2: Transferring data from admins to accounts...")
    cur.execute("""
        UPDATE accounts a JOIN admins adm ON a.account_id = adm.account_id
        SET a.full_name = adm.full_name,
            a.phone = adm.phone,
            a.date_of_birth = adm.date_of_birth,
            a.gender = adm.gender,
            a.address = adm.address;
    """)
    print("Admins merged:", cur.rowcount)

    print("Step 3: Transferring data from staffs to accounts...")
    cur.execute("""
        UPDATE accounts a JOIN staffs st ON a.account_id = st.account_id
        SET a.full_name = st.full_name,
            a.phone = st.phone,
            a.date_of_birth = st.date_of_birth,
            a.gender = st.gender,
            a.address = st.address;
    """)
    print("Staffs merged:", cur.rowcount)

    print("Step 4: Transferring data from customers to accounts...")
    cur.execute("""
        UPDATE accounts a JOIN customers c ON a.account_id = c.account_id
        SET a.full_name = c.full_name,
            a.phone = c.phone,
            a.date_of_birth = c.date_of_birth,
            a.gender = c.gender,
            a.address = c.address,
            a.playing_level = c.playing_level;
    """)
    print("Customers merged:", cur.rowcount)

    print("Step 5: Remapping FK values to accounts.account_id...")
    cur.execute("""
        UPDATE customer_preferences cp JOIN customers c ON cp.customer_id = c.customer_id
        SET cp.customer_id = c.account_id;
    """)
    print("Preferences remapped:", cur.rowcount)

    cur.execute("""
        UPDATE feedbacks f JOIN customers c ON f.customer_id = c.customer_id
        SET f.customer_id = c.account_id;
    """)
    print("Feedbacks remapped:", cur.rowcount)

    cur.execute("""
        UPDATE survey_recipients sr JOIN customers c ON sr.customer_id = c.customer_id
        SET sr.customer_id = c.account_id;
    """)
    print("Survey recipients remapped:", cur.rowcount)

    print("Step 6: Updating FK constraints...")
    try:
        cur.execute("ALTER TABLE customer_preferences DROP FOREIGN KEY fk_customer_preferences_customer;")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE feedbacks DROP FOREIGN KEY fk_feedbacks_customer;")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE survey_recipients DROP FOREIGN KEY fk_survey_recipients_customer;")
    except Exception:
        pass

    cur.execute("""
        ALTER TABLE customer_preferences
        ADD CONSTRAINT fk_customer_preferences_account
        FOREIGN KEY (customer_id) REFERENCES accounts (account_id) ON DELETE CASCADE ON UPDATE CASCADE;
    """)
    cur.execute("""
        ALTER TABLE feedbacks
        ADD CONSTRAINT fk_feedbacks_customer
        FOREIGN KEY (customer_id) REFERENCES accounts (account_id) ON DELETE RESTRICT ON UPDATE CASCADE;
    """)
    cur.execute("""
        ALTER TABLE survey_recipients
        ADD CONSTRAINT fk_survey_recipients_customer
        FOREIGN KEY (customer_id) REFERENCES accounts (account_id) ON DELETE RESTRICT ON UPDATE CASCADE;
    """)

    print("Step 7: Dropping old tables admins, staffs, customers...")
    try:
        cur.execute("ALTER TABLE admins DROP FOREIGN KEY fk_admins_account;")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE staffs DROP FOREIGN KEY fk_staffs_account;")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE customers DROP FOREIGN KEY fk_customers_account;")
    except Exception:
        pass
    cur.execute("DROP TABLE IF EXISTS admins;")
    cur.execute("DROP TABLE IF EXISTS staffs;")
    cur.execute("DROP TABLE IF EXISTS customers;")

    cur.execute("SET FOREIGN_KEY_CHECKS=1;")
    conn.commit()
    print("Migration completed successfully!")
except Exception as e:
    conn.rollback()
    print("Error during migration:", e)
    raise
finally:
    conn.close()
