import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QDateEdit, QMessageBox
from PyQt5.QtCore import QDate
from datetime import datetime


class PriceManagerApp(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize SQLite database
        self.init_db()

        # Initialize UI
        self.init_ui()

    def init_db(self):
        # Create or open the database
        self.conn = sqlite3.connect('price_manager.db')
        self.cursor = self.conn.cursor()

        # Create a table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                bought_date DATE,
                price REAL
            )
        ''')

    def init_ui(self):
        self.setWindowTitle('Price Manager')
        self.setGeometry(100, 100, 600, 500)

        self.layout = QVBoxLayout()

        # Label and input field for item name
        self.name_label = QLabel('Item Name:', self)
        self.layout.addWidget(self.name_label)

        self.name_input = QLineEdit(self)
        self.layout.addWidget(self.name_input)

        # Label and input field for bought date with date picker
        self.date_label = QLabel('Bought Date:', self)
        self.layout.addWidget(self.date_label)

        self.date_input = QDateEdit(self)
        self.date_input.setDisplayFormat('yyyy-MM-dd')
        self.date_input.setDate(QDate.currentDate())
        self.layout.addWidget(self.date_input)

        # Label and input field for price
        self.price_label = QLabel('Price:', self)
        self.layout.addWidget(self.price_label)

        self.price_input = QLineEdit(self)
        self.layout.addWidget(self.price_input)

        # Button to add item to manager
        self.add_button = QPushButton('Add Item', self)
        self.add_button.clicked.connect(self.add_item)
        self.layout.addWidget(self.add_button)

        # Button to delete selected item
        self.delete_button = QPushButton('Delete Selected Item', self)
        self.delete_button.clicked.connect(self.delete_item)
        self.layout.addWidget(self.delete_button)

        # Table to show added items
        self.table = QTableWidget(self)
        # Columns: Item Name, Bought Date, Price, Days Since, Mean Price per Day
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Item Name', 'Bought Date', 'Price', 'Days Since', 'Mean Price per Day'])
        self.layout.addWidget(self.table)

        # Label to display the total price of all items
        self.sum_label = QLabel('Total Price: 0.00', self)
        self.layout.addWidget(self.sum_label)

        # Label to display the sum of the mean price per day values for all items
        self.mean_label = QLabel('Sum of Mean Price per Day: 0.00', self)
        self.layout.addWidget(self.mean_label)

        # Set the layout
        self.setLayout(self.layout)

        # Load items from the database into the table
        self.load_items()

    def add_item(self):
        name = self.name_input.text().strip()
        price_str = self.price_input.text().strip()

        # Get the date from QDateEdit
        bought_date = self.date_input.date().toPyDate()

        try:
            # Parse the price input
            price = float(price_str)
            today = datetime.now().date()
            days_since = (today - bought_date).days
            # Calculate mean price per day for this item
            mean_price_per_day = price / days_since if days_since > 0 else 0

            # Save the item to the database
            self.cursor.execute('''
                INSERT INTO items (name, bought_date, price) VALUES (?, ?, ?)
            ''', (name, bought_date, price))
            self.conn.commit()

            # Add item to the table
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(name))
            self.table.setItem(row_position, 1, QTableWidgetItem(bought_date.strftime('%Y-%m-%d')))
            self.table.setItem(row_position, 2, QTableWidgetItem(f"{price:.2f}"))
            self.table.setItem(row_position, 3, QTableWidgetItem(str(days_since)))
            self.table.setItem(row_position, 4, QTableWidgetItem(f"{mean_price_per_day:.2f}"))

            # Clear the input fields and reset the date picker to today's date
            self.name_input.clear()
            self.price_input.clear()
            self.date_input.setDate(QDate.currentDate())

            # Update totals after adding an item
            self.update_totals()

        except ValueError:
            QMessageBox.warning(self, 'Invalid Input', 'Please enter a valid price.')

    def load_items(self):
        # Clear the table before loading items
        self.table.setRowCount(0)
        self.cursor.execute('SELECT id, name, bought_date, price FROM items')
        rows = self.cursor.fetchall()
        today = datetime.now().date()

        for row in rows:
            item_id, name, bought_date, price = row
            bought_date_obj = datetime.strptime(bought_date, '%Y-%m-%d').date()
            days_since = (today - bought_date_obj).days
            mean_price_per_day = price / days_since if days_since > 0 else 0

            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(name))
            self.table.setItem(row_position, 1, QTableWidgetItem(bought_date))
            self.table.setItem(row_position, 2, QTableWidgetItem(f"{price:.2f}"))
            self.table.setItem(row_position, 3, QTableWidgetItem(str(days_since)))
            self.table.setItem(row_position, 4, QTableWidgetItem(f"{mean_price_per_day:.2f}"))

        # Update totals after loading items
        self.update_totals()

    def update_totals(self):
        # Update total price of all items
        self.cursor.execute("SELECT SUM(price) FROM items")
        result = self.cursor.fetchone()[0]
        total_price = result if result is not None else 0
        self.sum_label.setText(f"Total Price: {total_price:.2f}")

        # Compute the sum of mean price per day values for all items.
        # For each item, mean price per day is (price / days_since) if days_since > 0, otherwise 0.
        self.cursor.execute("SELECT bought_date, price FROM items")
        rows = self.cursor.fetchall()
        total_mean = 0
        today = datetime.now().date()
        for row in rows:
            bought_date_str, price = row
            bought_date_obj = datetime.strptime(bought_date_str, '%Y-%m-%d').date()
            days_since = (today - bought_date_obj).days
            if days_since > 0:
                total_mean += price / days_since
            # If days_since is 0, we add 0 (as done in the row calculation)

        self.mean_label.setText(f"Sum of Mean Price per Day: {total_mean:.2f}")

    def delete_item(self):
        # Get the selected row
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            # Use the item name (assumed unique) from the first column as identifier
            item_name = self.table.item(selected_row, 0).text()

            # Confirm deletion
            reply = QMessageBox.question(
                self,
                'Delete Item',
                f"Are you sure you want to delete '{item_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Delete from the database
                self.cursor.execute('DELETE FROM items WHERE name = ?', (item_name,))
                self.conn.commit()

                # Remove the item from the table
                self.table.removeRow(selected_row)

                # Update totals after deletion
                self.update_totals()
        else:
            QMessageBox.warning(self, 'No Selection', 'Please select an item to delete.')

    def closeEvent(self, event):
        # Close the database connection when the app is closed
        self.conn.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_window = PriceManagerApp()
    app_window.show()
    sys.exit(app.exec_())