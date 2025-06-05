# SingleCraft | Pre-Alpha

SingleCraft is a powerful minecrafts server hosting in Python.

# How to use ?

Singlecraft need a MySQL database for save server configuration (Like, launch jar, server name, and much more)

So, for now, we need to add yourself the line `DatabaseManager.SetupDatabase()` at the `@app.route('/')` line
When you have launched the website, go to the root page (E.g: localhost:5000/).

So remove the line `DatabaseManager.SetupDatabase()` when your database is correctly setup !

## Goal

- a settings page for change multiple configurations. ❌

- a page for add plugins & mods (With filter for only display usable jar). ❌

- a dropdown in the server's page for select the correct jar. **(Require the settings page)** ❌

- Upgrade the UI/UX of all pages. ❌

- a simplfied installer. ❌

## F.A.Q

- Any simplified installation process in the futur?
  Yes.

*I will add more frequently asked questions later!*

## License
This project is proprietary software. All rights reserved.
No distribution, modification, or commercial use is allowed without explicit permission.
