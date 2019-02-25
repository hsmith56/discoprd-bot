const Discord = require('discord.js')
const client = new Discord.Client()
client.on("ready", () => {
  // This event will run if the bot starts, and logs in, successfully.
  console.log(`Bot has started, with ${client.users.size} users, in ${client.channels.size} channels of ${client.guilds.size} guilds.`); 
  // Example of changing the bot's playing game to something useful. `client.user` is what the
  // docs refer to as the "ClientUser".
  client.user.setActivity(`Serving ${client.guilds.size} servers`);
  
});

var badwords = ['nigger','nigge r','nigg er','nig ger','ni gger','n igger','n i g g e r','n i g g er','n i g ger','n i gger','n i gge r','n i gg e r','n igg e r','ni gg e r','n ig g er','n ig ge r','n ig ger','n i gger','n i gge r','n i gg er','n i gg e r','n igge r','n igg e r','n igg er','n ig ger','n ig g er','n ig g e r','ni g ger','ni g g er ','ni g g e r','nig g e r','nigg e r'];
client.on('message', msg => {
  if (msg.content === '69') {
    msg.reply('no')
	//channel.send('bop')
	msg.delete().catch(console.error);
	msg.guild.members.get("512473233078091798").setNickname("Mo Bomba");
  }
    
  if (msg.content.includes('!change')) {
	var text = "";
	var possible = "abcdef0123456789";
	var num = Math.floor(Math.random() * 8) + 1
	for (var i = 0; i < num; i++)
		text += possible.charAt(Math.floor(Math.random() * possible.length));
	
	for (var i = 0 ; i < 10; i++) 	
		msg.guild.members.get("512473233078091798").setNickname('0x' + text);
		console.log('0x' + text);
	}  
  
	// msg.delete().catch(console.error);
  if (msg.content === 'fuck') {
	  msg.reply('SHIT. BITCH.')
	  //msg.delete().catch(console.error);
  }  
 

	for (var i =0; i < badwords.length; i ++) {
		if (msg.content.toLowerCase().includes(badwords[i])) {
		  msg.delete().catch(console.error);
		}	
	}  
})

client.on('voiceStateUpdate', (oldMember, newMember, message) => {
  let newUserChannel = newMember.voiceChannel
  let oldUserChannel = oldMember.voiceChannel
  var oldId = oldMember['user']['id']
  var newId = newMember['user']['id']
  
  if (!(oldMember['user']['bot']) === 'True') {
	 
  
  if(oldUserChannel === undefined && newUserChannel !== undefined) {
	//client.channels.get('509088508166537250').send('hi <@'+ (newMember['user']['username']));
	client.channels.get('509088508166537250').send('hi <@'+ oldId + '>');
	
  } else if(newUserChannel === undefined){
	//client.channels.get('509088508166537250').send('bye @' + (oldMember['user']['username']));
	client.channels.get('509088508166537250').send('bye <@'+ newId + '>');
    //console.log(newMember['nickname']);
	console.log(oldMember['user']['username'])
  }
  }
})


client.login('NTEyNDczMjMzMDc4MDkxNzk4.D05DsQ.Rl3H11DlsTYjF9cEj_07-yflCnU')
