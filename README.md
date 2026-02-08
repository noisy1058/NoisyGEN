# NoisyGEN

Automated software that allows user to generate icloud hidden mails that are automatically redirected to your main icloud mail.  

Behaviour:  

- First time running: when you introduce the number of mails you want to generate, it will ask you to manually make login in your icloud account (remember  to tick keep alive session checkbox). After logging in it will automatically close chromium tab and will continue with the mails creation without interface.  

- Second time: you will see that after the first time you run it a file called "settings.json" that contains your cookies information about login will appear (this will help to skip login in your icloud account), so you will only have to introduce the number of mails you want to gen.

- IMPORTANT: remember that icloud only allows users to generate 5 mails per hour, bot will automatically handle this by genning the accounts in rounds of 5, after 5 genned accounts it will wait 1 hour and 5 seconds to gen the next accounts.