import pickle
from collections import UserDict
from datetime import datetime, date, timedelta


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Name can't be empty.")
        super().__init__(value.strip())


class Phone(Field):
    def __init__(self, value):
        v = str(value).strip()
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Phone must contain exactly 10 digits.")
        super().__init__(v)


class Birthday(Field):
    def __init__(self, value):
        try:
            if isinstance(value, date):
                dt = value
            else:
                dt = datetime.strptime(str(value).strip(), "%d.%m.%Y").date()
            super().__init__(dt)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
        
    def add_phone(self, phone_str):
        self.phones.append(Phone(phone_str))

    def remove_phone(self, phone_str):
        for p in self.phones:
            if p.value == phone_str:
                self.phones.remove(p)
                return True
        return False

    def edit_phone(self, old_phone, new_phone):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return True
        return False

    def find_phone(self, phone_str):
        for p in self.phones:
            if p.value == phone_str:
                return p
        return None

    def add_birthday(self, bd_str):
        self.birthday = Birthday(bd_str)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones) if self.phones else "-"
        bd = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "-"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {bd}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days_ahead=7):
        today = date.today()
        end_day = today + timedelta(days=days_ahead)
        result = []
        for rec in self.data.values():
            if not rec.birthday:
                continue
            bd: date = rec.birthday.value
            candidate = bd.replace(year=today.year)
            if candidate < today:
                candidate = bd.replace(year=today.year + 1)

            if today <= candidate <= end_day:
                congr_date = candidate
                if congr_date.weekday() == 5:
                    congr_date += timedelta(days=2)
                elif congr_date.weekday() == 6:
                    congr_date += timedelta(days=1)

                result.append({
                    "name": rec.name.value,
                    "congratulation_date": congr_date.strftime("%Y.%m.%d"),
                })
        result.sort(key=lambda x: x["congratulation_date"])
        return result


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"Value error: {e}"
        except AttributeError:
            return "This contact does not exist."
        except IndexError:
            return "Not enough arguments."
        except Exception as e:
            return f"Error: {e}"
    return inner


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    msg = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        msg = "Contact added."
    if phone:
        record.add_phone(phone)
    return msg


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    rec = book.find(name)
    if rec.edit_phone(old_phone, new_phone):
        return "Phone updated."
    return "Old phone not found."


@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    rec = book.find(name)
    if not rec.phones:
        return "No phones."
    return "; ".join(p.value for p in rec.phones)


@input_error
def show_all(args, book: AddressBook):
    if not book.data:
        return "No contacts."
    return "\n".join(str(r) for r in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    name, bd_str, *_ = args
    rec = book.find(name)
    if rec is None:
        rec = Record(name)
        book.add_record(rec)
        prefix = "Contact created. "
    else:
        prefix = ""
    rec.add_birthday(bd_str)
    return prefix + "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    rec = book.find(name)
    return rec.birthday.value.strftime("%d.%m.%Y") if rec.birthday else "No birthday set."


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays(7)
    if not upcoming:
        return "No birthdays in the next 7 days."
    grouped = {}
    for item in upcoming:
        grouped.setdefault(item["congratulation_date"], []).append(item["name"])
    return "\n".join(f"{day}: {', '.join(names)}" for day, names in grouped.items())


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    print("Commands: add, change, phone, all, add-birthday, show-birthday, birthdays, hello, close/exit")

    while True:
        user_input = input("Enter a command: ")
        command, *args = user_input.strip().split(maxsplit=1)
        args = args[0].split() if args else []

        if command in ("close", "exit"):
            save_data(book)
            print("Data saved. Good bye!")
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
            print(show_all(args, book))
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