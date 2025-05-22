from collections import UserDict
from datetime import datetime, timedelta
import pickle

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

class Field:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def __str__(self):
        return str(self._value)

class Name(Field):
    def __init__(self, value):
        super().__init__(value)
        if not value:
            raise ValueError("Name cannot be empty")

class Phone(Field):
    def __init__(self, value):
        super().__init__(value)
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain 10 digits")

class Birthday(Field):
    def __init__(self, value):
        super().__init__(value)
        try:
            datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    @property
    def value(self):
        return datetime.strptime(super().value, "%d.%m.%Y").date()

    @value.setter
    def value(self, new_value):
        try:
            datetime.strptime(new_value, "%d.%m.%Y")
            super().value = new_value
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        p = self.find_phone(phone)
        if p:
            self.phones.remove(p)
        else:
            raise ValueError(f"Phone number {phone} not found")

    def edit_phone(self, old_phone, new_phone):
        p = self.find_phone(old_phone)
        if p:
            try:
                p.value = Phone(new_phone).value
            except ValueError:
                raise ValueError(f"Invalid new phone number {new_phone}")
        else:
            raise ValueError(f"Phone number {old_phone} not found")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        try:
            self.birthday = Birthday(birthday)
        except ValueError as e:
            print(e)

    def show_birthday(self):
        return self.birthday.value.strftime("%d.%m.%Y") if self.birthday else None

    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones)
        birthday_str = f", birthday: {self.birthday.value.strftime('%d.%m.%Y')}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.now().date()
        upcoming_birthdays = []
        for name, record in self.data.items():
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                delta = birthday_this_year - today
                if 0 <= delta.days < 7:
                    greeting_date = birthday_this_year
                    if greeting_date.weekday() >= 5:  # Saturday or Sunday
                        days_to_add = 0
                        if greeting_date.weekday() == 5:  # Saturday
                            days_to_add = 2
                        elif greeting_date.weekday() == 6:  # Sunday
                            days_to_add = 1
                        greeting_date += timedelta(days=days_to_add)
                    upcoming_birthdays.append({"name": name, "birthday": greeting_date.strftime("%Y.%m.%d")})
        return upcoming_birthdays

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())

def parse_input(user_input):
    if not user_input:
        return "", []  # Повертає порожню команду та порожній список аргументів
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Invalid command format. Please try again."
        except Exception as e:
            return f"An unexpected error occurred: {e}"
    return inner

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Contact updated."
    else:
        raise KeyError

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        return f"{name}: {'; '.join(p.value for p in record.phones)}"
    else:
        raise KeyError

@input_error
def show_all(book: AddressBook):
    if book:
        return str(book)
    else:
        return "The address book is empty."

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added."
    else:
        raise KeyError

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        birthday = record.show_birthday()
        return f"{name}'s birthday: {birthday}" if birthday else f"{name}'s birthday is not set."
    else:
        raise KeyError

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if upcoming:
        result = "Upcoming birthdays:\n"
        birthdays_by_day = {}
        for item in upcoming:
            day = datetime.strptime(item['birthday'], "%Y.%m.%d").strftime("%A %d.%m")
            if day not in birthdays_by_day:
                birthdays_by_day[day] = []
            birthdays_by_day[day].append(item['name'])

        for day, names in sorted(birthdays_by_day.items(), key=lambda item: datetime.strptime(item[0].split()[1], "%d.%m").date().timetuple().tm_yday):
            result += f"{day}: {', '.join(names)}\n"
        return result.strip()
    else:
        return "No upcoming birthdays in the next 7 days."

def main():
    book = load_data()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
