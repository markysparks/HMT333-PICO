import machine
import settings
import calibration


def do_setup(uart1):
    """
    Performs the setup routine by entering the setup mode and allowing the
    user to update SETTINGS and CORRECTIONS dictionaries.

        The function prompts the user to press 's' to enter the setup mode.
        If the 's' key is pressed within 30 seconds, the function proceeds
        with the setup routine. Once in the setup mode, the user is
        presented with options to exit the function ('x'), update SETTINGS (
        'u'), or update CORRECTIONS ('c'). The user can enter the
        corresponding keys to perform the desired action.

        If the user chooses to update SETTINGS, each key in the SETTINGS
        dictionary is iterated over, and the user is prompted to enter a new
        value for each key. The function validates and updates the entered
        values according to specific requirements for certain keys (
        'REPORTING_SCHED', 'WOW_AUTH_KEY').

        The updated SETTINGS dictionary is saved to the settings.py file,
        and the updated keys and values are written to the UART port. If the
        user chooses to update CORRECTIONS, each key in the CORRECTIONS
        dictionary is iterated over, and the user is prompted to enter a new
        value. The function validates and updates the entered values to
        ensure they are numeric. The updated CORRECTIONS dictionary is saved
        to the calibration.py file, and the updated keys and values are
        written to the UART port.

        Parameters:
            uart1 - UART port that has been initialised.

        Returns:
            None
        """
    uart1.write("\r\nPress 's' to enter SETUP\r\n")
    key_pressed = uart1.read(1)  # Read a single character from UART1

    if key_pressed == b's':  # Check if the received character is 's'
        uart1.write("Entering SETUP...\r\n")
    else:
        uart1.write("No 's' key pressed. Commencing startup....\r\n")
        return

    uart1.write(
        "\r\nPress :"
        "\r\n'x' to EXIT and continue startup"
        "\r\n'u' to update SETTINGS and (optionally) CALIBRATION COEFFICIENTS"
        "\r\n'c' to update CALIBRATION COEFFICIENTS only...\r\n")

    try:
        while True:
            # Check if there are any characters available to read
            if uart1.any():
                data = uart1.read(1)  # Read a single character from UART1
                if data == b'x':  # Check if the received character is 'x'
                    print("Exiting the function...")
                    uart1.write("Starting up...\r\n")
                    return  # Exit the function

                elif data == b'u':  # Check if the received character is 'u'
                    print("Updating SETTINGS...")

                    for key, value in sorted(settings.SETTINGS.items()):
                        uart1.write(
                            "\r\nCurrent value "
                            "for {}: {}\r\n".format(key, value))
                        uart1.write("Enter new value for {}: ".format(key))
                        new_value = ""
                        while True:
                            char = uart1.read(1)
                            # Check if the Enter key was pressed
                            if char == b'\r':
                                uart1.write("\r\n")
                                break
                            uart1.write(char)
                            new_value += char.decode()

                        new_value = new_value.strip()

                        if key == "REPORTING_SCHED":
                            if new_value:
                                while new_value not in ['1', '2', '3']:
                                    uart1.write(
                                        "Invalid value! Only '1', '2', or '3' "
                                        "are allowed. Please enter again: ")
                                    new_value = ""
                                    while True:
                                        char = uart1.read(1)
                                        # Check if the Enter key was pressed
                                        if char == b'\r':
                                            uart1.write("\r\n")
                                            break
                                        uart1.write(char)
                                        new_value += char.decode()
                                    new_value = new_value.strip()
                            else:
                                uart1.write(
                                    "Keeping the old value "
                                    "for {}\r\n".format(key))
                                continue

                        elif key == "WOW_AUTH_KEY":
                            if new_value:
                                while not new_value.isdigit() or len(
                                        new_value) != 6:
                                    uart1.write(
                                        "Invalid value! Please enter a "
                                        "6-digit number. Please enter again: ")
                                    new_value = ""
                                    while True:
                                        char = uart1.read(1)
                                        # Check if the Enter key was pressed
                                        if char == b'\r':
                                            uart1.write("\r\n")
                                            break
                                        uart1.write(char)
                                        new_value += char.decode()
                                    new_value = new_value.strip()
                            else:
                                uart1.write(
                                    "Keeping the old value "
                                    "for {}\r\n".format(key))
                                continue

                        if new_value:
                            settings.SETTINGS[key] = new_value
                            uart1.write(
                                "Updated {} to: {}\r\n".format(key, new_value))
                        else:
                            uart1.write(
                                "Keeping the old value for {}\r\n".format(key))

                    # Save changes to settings.py file
                    with open("settings.py", "w") as file:
                        file.write("SETTINGS = {}\n".format(settings.SETTINGS))

                    uart1.write("\r\nSETTINGS updated:\r\n")
                    for key, value in sorted(settings.SETTINGS.items()):
                        uart1.write("{}: {}\r\n".format(key, value))

                    uart1.write("\r\nDo you want to "
                                "update CALIBRATION COEFFICIENTS? (y/n): ")
                    update_corrections = uart1.read(1)
                    if update_corrections == b'\n':
                        update_corrections = uart1.read(1)
                    print(update_corrections)
                    if update_corrections == b'y':
                        data = b'c'
                    else:
                        uart1.write("\r\nStarting up...")
                        return

                if data == b'c':  # Check if the received character is 'c'
                    print("Updating CORRECTIONS...")

                    for key, value in sorted(calibration.CORRECTIONS.items()):
                        uart1.write(
                            "\r\nCurrent value "
                            "for {}: {}\r\n".format(key, value))
                        uart1.write("Enter new value for {}: ".format(key))
                        new_value = ""
                        while True:
                            char = uart1.read(1)
                            # Check if the Enter key was pressed
                            if char == b'\r':
                                uart1.write("\r\n")
                                break
                            uart1.write(char)
                            new_value += char.decode()

                        new_value = new_value.strip()

                        if new_value:
                            # Calibration coefficients must be integers/floats
                            while not (new_value.isdigit()
                                       or '.' in new_value):
                                uart1.write(
                                    "Invalid value! Please enter a number. "
                                    "Please enter again: ")
                                new_value = ""
                                while True:
                                    char = uart1.read(1)
                                    # Check if the Enter key was pressed
                                    if char == b'\r':
                                        uart1.write("\r\n")
                                        break
                                    uart1.write(char)
                                    new_value += char.decode()
                                new_value = new_value.strip()
                        else:
                            uart1.write(
                                "Keeping the old value for {}\r\n".format(key))
                            continue

                        if new_value:
                            calibration.CORRECTIONS[key] = new_value
                            uart1.write(
                                "Updated {} to: {}\r\n".format(key, new_value))
                        else:
                            uart1.write(
                                "Keeping the old value for {}\r\n".format(key))

                    # Save changes to calibration.py file
                    with open("calibration.py", "w") as file:
                        file.write(
                            "CORRECTIONS = "
                            "{}\n".format(calibration.CORRECTIONS))

                    uart1.write("\r\nCORRECTIONS updated:\r\n")
                    for key, value in sorted(calibration.CORRECTIONS.items()):
                        uart1.write("{}: {}\r\n".format(key, value))

                    uart1.write('\r\nStarting up...')
                return
    except TypeError:
        # If the user has not entered anything in a settings field for
        # a period longer than the UART timeout, restart - a TypeError will
        # be generated because there will be no characters in the UART buffer.
        machine.reset()
