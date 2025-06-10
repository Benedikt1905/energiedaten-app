# energiedaten-app
The energiedaten-app is a professional desktop application with a graphical user interface (GUI) that analyses, checks and visualizes the primary energy consumption of various European countries from CSV, JSON, SQLite and API data sources. The app is aimed at users who value data security, error handling, data visualization and statistical evaluation.

If their are needed modules who aren't installed yet, see install requirements.txt for an installing guide

Features are:
- CSV security check:

- Automatic detection of potentially dangerous content such as:

- Formulas like (=, @, cmd, powershell, and more...)

- Unicode control characters (e.g. RTL overrides)

- SQL injection patterns (DROP, DELETE, etc.)

- Display of a security warning + log entry in the event of a threat.

- Statistical evaluation of the maximum annual consumption of the selected energy source and diplay in the GUI.

- Statistical evaluation of the minimum annual consumption of the selected energy source.

- Statistical evaluation of the average annual consumption of the selected energy source.

- GUI with tkinter

- Dropdownmenues for the country, energy source and year

- Logging System with log level INFO, Warning and Error

- Error Messages with tkinter.messagebox

- Logo and icon integration

- API integration, get data vi API

- Use API data, JSON data, CSV data and DB data, files

- GUI with a 3D pie chart, displaying the parts of the energy sources in different colors, in percantage and labels


- A Table in 2 switching colors where the data is displayed, displaying the data for the selected country in a table 

- Typconvertation 

- Field empty detection

- Scrollbar for the table

- Sorting the table with click on a year or a energy source

- Start and Shutdown logs

- Structur with img folder for images, log folder for logs and data folder where the data is stored

- install requirements.txt, a guide to install required dependencie packages for using the app in 8 different languages

- github repository with 8 releases

- local API configuration with a json file

- testing file for developing

- create logs folder if doesnt exist

- .gitignore file

- Comments in the code to make the code more readbilitie

- A github repository with issues, bug tracker, branches, commits to detect progress

- Error handling with different types of file formates

If you have any questions please contact me.
