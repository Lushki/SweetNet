import bcrypt

class PasswordManager:

    @staticmethod
    def hash_password(password):
        """
        Hashes the password using bcrypt and returns the salt and hashed password.
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return salt, hashed_password

    @staticmethod
    def verify_password(entered_password, salt, hashed_password):
        """
        Verifies the entered password against the stored hashed password using the stored salt.
        """
        hashed_entered_password = bcrypt.hashpw(entered_password.encode('utf-8'), salt)
        return hashed_entered_password == hashed_password

    @staticmethod
    def hash_new_password(new_password):
        """
        Hashes the new password using bcrypt and returns the new salt and new hashed password.
        """
        salt = bcrypt.gensalt()
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        return salt, hashed_new_password
