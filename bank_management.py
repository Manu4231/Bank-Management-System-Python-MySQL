
import mysql.connector
from decimal import Decimal, InvalidOperation


# 1. Connect Python to MySQL
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="pushpendra@2023",
        database="bank_management"
    )


# 2. Create a new bank account
def create_account():
    name = input("Enter customer name: ").strip()
    phone = input("Enter phone number: ").strip()

    if not name:
        print("Customer name cannot be empty.")
        return

    try:
        con = connect_db()
        cur = con.cursor()

        cur.execute(
            "INSERT INTO accounts (customer_name, phone) "
            "VALUES (%s, %s)",
            (name, phone or None)
        )

        account_no = cur.lastrowid
        con.commit()

        print("\nAccount created successfully!")
        print("Your account number is:", account_no)
        print("Opening balance: Rs. 0.00")

    except mysql.connector.Error as err:
        print("Database error:", err)

    finally:
        if "cur" in locals():
            cur.close()
        if "con" in locals() and con.is_connected():
            con.close()


# 3. View account details
def view_account():
    account_no = input("Enter account number: ").strip()

    if not account_no.isdigit():
        print("Invalid account number.")
        return

    con = None
    cur = None

    try:
        con = connect_db()
        cur = con.cursor()

        cur.execute(
            "SELECT account_id, customer_name, phone, balance "
            "FROM accounts WHERE account_id = %s",
            (int(account_no),)
        )

        account = cur.fetchone()

        if account:
            print("\n--- ACCOUNT DETAILS ---")
            print("Account number:", account[0])
            print("Customer name:", account[1])
            print("Phone:", account[2] or "Not provided")
            print("Balance: Rs.", account[3])
        else:
            print("Account not found.")

    except mysql.connector.Error as err:
        print("Database error:", err)

    finally:
        if cur:
            cur.close()
        if con and con.is_connected():
            con.close()


# 4. Deposit or withdraw money
def perform_transaction(transaction_type):
    account_no = input("Enter account number: ").strip()

    if not account_no.isdigit():
        print("Invalid account number.")
        return

    try:
        amount = Decimal(input("Enter amount: ").strip())

        if not amount.is_finite() or amount <= 0:
            print("Amount must be greater than zero.")
            return

        if amount.as_tuple().exponent < -2:
            print("Enter an amount with at most 2 decimal places.")
            return

    except InvalidOperation:
        print("Please enter a valid amount.")
        return

    con = None
    cur = None

    try:
        con = connect_db()
        cur = con.cursor()

        # Start a database transaction and lock this account row
        cur.execute(
            "SELECT balance FROM accounts "
            "WHERE account_id = %s FOR UPDATE",
            (int(account_no),)
        )

        result = cur.fetchone()

        if result is None:
            print("Account not found.")
            con.rollback()
            return

        balance = result[0]

        if transaction_type == "WITHDRAW" and amount > balance:
            print("Insufficient balance.")
            con.rollback()
            return

        if transaction_type == "DEPOSIT":
            new_balance = balance + amount
        else:
            new_balance = balance - amount

        cur.execute(
            "UPDATE accounts SET balance = %s "
            "WHERE account_id = %s",
            (new_balance, int(account_no))
        )

        cur.execute(
            "INSERT INTO transactions "
            "(account_id, transaction_type, amount, balance_after) "
            "VALUES (%s, %s, %s, %s)",
            (int(account_no), transaction_type, amount, new_balance)
        )

        # Save balance and transaction together
        con.commit()

        print("\nTransaction successful!")
        print("Transaction type:", transaction_type)
        print("Transaction amount: Rs.", amount)
        print("Available balance: Rs.", new_balance)

    except mysql.connector.Error as err:
        if con and con.is_connected():
            con.rollback()
        print("Transaction failed:", err)

    finally:
        if cur:
            cur.close()
        if con and con.is_connected():
            con.close()


# 5. Check balance
def check_balance():
    account_no = input("Enter account number: ").strip()

    if not account_no.isdigit():
        print("Invalid account number.")
        return

    con = None
    cur = None

    try:
        con = connect_db()
        cur = con.cursor()

        cur.execute(
            "SELECT customer_name, balance FROM accounts "
            "WHERE account_id = %s",
            (int(account_no),)
        )

        result = cur.fetchone()

        if result:
            print("Customer:", result[0])
            print("Current balance: Rs.", result[1])
        else:
            print("Account not found.")

    except mysql.connector.Error as err:
        print("Database error:", err)

    finally:
        if cur:
            cur.close()
        if con and con.is_connected():
            con.close()


# 6. View transaction history
def transaction_history():
    account_no = input("Enter account number: ").strip()

    if not account_no.isdigit():
        print("Invalid account number.")
        return

    con = None
    cur = None

    try:
        con = connect_db()
        cur = con.cursor()

        cur.execute(
            "SELECT transaction_id, transaction_type, amount, "
            "balance_after, transaction_date "
            "FROM transactions WHERE account_id = %s "
            "ORDER BY transaction_id DESC",
            (int(account_no),)
        )

        records = cur.fetchall()

        if not records:
            print("No transactions found.")
            return

        print("\n--- TRANSACTION HISTORY ---")

        for record in records:
            print(
                f"ID: {record[0]} | "
                f"Type: {record[1]} | "
                f"Amount: Rs. {record[2]} | "
                f"Balance: Rs. {record[3]} | "
                f"Date: {record[4]}"
            )

    except mysql.connector.Error as err:
        print("Database error:", err)

    finally:
        if cur:
            cur.close()
        if con and con.is_connected():
            con.close()


# 7. Main menu
def main():
    while True:
        print("\n===== BANK MANAGEMENT SYSTEM =====")
        print("1. Create Account")
        print("2. View Account Details")
        print("3. Deposit Money")
        print("4. Withdraw Money")
        print("5. Check Balance")
        print("6. Transaction History")
        print("7. Exit")

        choice = input("Enter your choice (1-7): ").strip()

        if choice == "1":
            create_account()
        elif choice == "2":
            view_account()
        elif choice == "3":
            perform_transaction("DEPOSIT")
        elif choice == "4":
            perform_transaction("WITHDRAW")
        elif choice == "5":
            check_balance()
        elif choice == "6":
            transaction_history()
        elif choice == "7":
            print("Thank you for using Bank Management System!")
            break
        else:
            print("Invalid choice. Please select 1 to 7.")


if __name__ == "__main__":
    main()
