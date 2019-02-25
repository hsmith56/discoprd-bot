const Discord = require('discord.js');

const client = new Discord.Client();

 

client.on('ready', () => {

    console.log('I am ready!');

});

 

client.on('message', message => {

    if (message.content === 'ping') {

       message.reply('pong');

       }

});

client.login(process.env.NTEyNDczMjMzMDc4MDkxNzk4.D05DsQ.Rl3H11DlsTYjF9cEj_07-yflCnU);//where BOT_TOKEN is the token of our bot
