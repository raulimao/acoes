import yaml
from yaml.loader import SafeLoader
from database import initialize_database, add_user, get_user

def migrate_users_from_yaml(yaml_file='config.yaml'):
    """
    Migrates users from a config.yaml file to the SQLite database.
    """
    initialize_database()

    try:
        with open(yaml_file) as file:
            config = yaml.load(file, Loader=SafeLoader)

        if 'credentials' in config and 'usernames' in config['credentials']:
            users_to_migrate = config['credentials']['usernames']

            print(f"Migrating {len(users_to_migrate)} users from {yaml_file} to database...")

            for username, user_data in users_to_migrate.items():
                name = user_data.get('name', '')
                email = user_data.get('email', '')
                password = user_data.get('password')

                if not password:
                    print(f"Skipping user '{username}': No password found.")
                    continue

                # Check if user already exists in the database
                if get_user(username):
                    print(f"Skipping user '{username}': Already exists in the database.")
                    continue

                try:
                    add_user(username, name, email, password)
                    print(f"User '{username}' migrated successfully.")
                except Exception as e:
                    print(f"Error migrating user '{username}': {e}")

            print("Migration complete.")

        else:
            print(f"No user credentials found in {yaml_file}.")

    except FileNotFoundError:
        print(f"Error: {yaml_file} not found.")
    except Exception as e:
        print(f"An error occurred during migration: {e}")

if __name__ == "__main__":
    migrate_users_from_yaml()