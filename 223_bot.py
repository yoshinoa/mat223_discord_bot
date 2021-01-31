import discord
import os
import json
from dotenv import load_dotenv
from typing import List, Tuple, Any

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
client = discord.Client(intents=intents)

partners = []
matching_groups = []
matched_groups = []


async def get_member(new_user, owo_client):
    for item in owo_client.guilds:
        test_item = await item.fetch_member(new_user.id)
        if test_item is not None:
            return test_item


async def single_double_group_maker(bitem, new_client):
    if len(bitem) == 1:
        get_user1 = await get_member(await new_client.fetch_user(bitem[0]), new_client)
        bemp_group = Group([get_user1], "single")
    elif len(bitem) == 2:
        get_user1 = await get_member(await new_client.fetch_user(bitem[0]), new_client)
        get_user2 = await get_member(await new_client.fetch_user(bitem[1]), new_client)
        bemp_group = Group([get_user1, get_user2], "double")
    return bemp_group


async def onstart(client_item):
    if os.path.exists("previous_session.json"):
        with open("previous_session.json") as json_file:
            json_data = json.load(json_file)
    for item in list(json_data["matching_groups"]):
        temp_group = await single_double_group_maker(item, client_item)
        matching_groups.append(temp_group)
    for item in list(json_data["matched_groups"]):
        temp_group1 = await single_double_group_maker(item[0], client_item)
        temp_group2 = await single_double_group_maker(item[1], client_item)
        matched_groups.append((temp_group1, temp_group2))


class Group:
    group_leader: discord.User
    group_members: List[discord.Member]
    status: str

    def __init__(self, group_members: List[discord.Member], status: str) -> None:
        """
        group_members is a list of two discord users, where the first element
        is the group leader

        status is either single or double
        """
        self.group_leader = group_members[0]
        self.group_members = group_members
        self.status = status

    def __str__(self):
        if self.status == "single":
            stringle1 = self.group_members[0].nick
            if stringle1 is None:
                stringle1 = self.group_members[0].name
            return f"{stringle1}"
        elif self.status == "double":
            stringle1 = self.group_members[0].nick
            stringle2 = self.group_members[0].nick
            if stringle1 is None:
                stringle1 = self.group_members[0].name
            if stringle2 is None:
                stringle2 = self.group_members[0].name
            return f"{self.group_members[0].nick} and {self.group_members[1].nick}"

    def contains_user(self, user_id: str):
        """
        given userid check it against group members
        """
        for users in self.group_members:
            if users.id == user_id:
                return True
        return False

    def get_ids(self):
        if self.status == "single":
            return self.group_members[0].id,
        elif self.status == "double":
            return self.group_members[0].id, self.group_members[1].id


def write_file():
    matched_group_ids = []
    matching_group_ids = []
    for item in matching_groups:
        matching_group_ids.append(item.get_ids())
    for item in matched_groups:
        matched_group_ids.append((item[0].get_ids(), item[1].get_ids()))
    writing_dict = {"matching_groups": matching_group_ids, "matched_groups": matched_group_ids}
    with open ("previous_session.json", "w") as json_file:
        json.dump(writing_dict, json_file)


def check_in_group(user_id: str) -> bool:
    for items in matching_groups:
        if items.contains_user(user_id):
            return True
    for group in matched_groups:
        for items in group:
            if items.contains_user(user_id):
                return True
    return False


async def partner_matching(message) -> None:
    if len(partners) == 2:
        await message.channel.send(f'Partner for {partners[0].mention} and {partners[1].mention} has been found!')
        dm_1 = await partners[0].create_dm()
        dm_2 = await partners[1].create_dm()
        await dm_1.send(f"Partner found! Contact {partners[1].mention} to work together.")
        await dm_2.send(f"Partner found! Contact {partners[0].mention} to work together.")
        partners.clear()


async def check_matching(message):
    if len(matching_groups) == 2:
        matched_groups.append((matching_groups[0], matching_groups[1]))
        matching_groups.clear()
        await message.channel.send(f'Group with leader {matched_groups[len(matched_groups)-1][0].group_leader.mention} has been paired with group with leader {matched_groups[len(matched_groups)-1][1].group_leader.mention}')
        for member in matched_groups[len(matched_groups)-1][0].group_members:
            private_channel = await member.create_dm()
            await private_channel.send(
                f"Your group has been paired! Contact {matched_groups[len(matched_groups)-1][1].group_leader.mention} to setup a time!"
            )
        for member in matched_groups[len(matched_groups)-1][1].group_members:
            private_channel = await member.create_dm()
            await private_channel.send(
                f"Your group has been paired! Contact {matched_groups[len(matched_groups)-1][0].group_leader.mention} to setup a time!"
            )


@client.event
async def on_ready():
    await onstart(client)
    print(matched_groups)
    print(matching_groups)
    await client.change_presence(activity=discord.Activity(name='status', details="Type !commands to see a list of commands", ))
    print(f"{client.user} has connected to discord!")


@client.event
async def on_message(message):
    if message.content[0:8] == '!partner':
        try:
            message.mentions[0]
        except IndexError:
            await message.channel.send(f"Input did not contain another user, please @ them.")
        if check_in_group(message.author.id) and check_in_group(message.mentions[0].id):
            await message.channel.send(f"You and {message.mentions[0].mention} are both already in groups, please disband your group(s) before joining another one.")
        elif check_in_group(message.author.id):
            await message.channel.send(f"You are already in a group, please disband your group before joining another one.")
        elif check_in_group(message.mentions[0].id):
            await message.channel.send(f"{message.mentions[0].mention} is already in a group, please ask them to disband their group before joining another one.")
        else:
            temp_group = Group([await get_member(message.author, client), await get_member(message.mentions[0], client)], "double")
            matching_groups.append(temp_group)
            await message.channel.send(f'{message.author.mention} partnered with {message.mentions[0].mention}')
            await check_matching(message)
            write_file()
    elif message.content[0:11] == '!individual':
        if check_in_group(message.author.id):
            await message.channel.send(f"You are already in a group, disband your group before you declare yourself as an individual.")
        else:
            temp_group = Group([await get_member(message.author, client)], "single")
            matching_groups.append(temp_group)
            await message.channel.send(f'{message.author.mention} is working individually.')
            await check_matching(message)
            write_file()
    elif message.content[0:8] == '!disband':
        if not check_in_group(message.author.id):
            await message.channel.send(f"You aren't in a group.")
        else:
            for items in matching_groups:
                if items.contains_user(message.author.id):
                    await message.channel.send(f'Group with {str(items[0])} has been disbanded.')
                    matching_groups.remove(items)
            for group in matched_groups:
                if group[0].contains_user(message.author.id):
                    await message.channel.send(f'Group with {str(group[0])} has been disbanded.')
                    await message.channel.send(f'Group with {str(group[1])} has been put back into the queue.')
                    matching_groups.append(group[1])
                    matched_groups.remove(group)
                elif group[1].contains_user(message.author.id):
                    await message.channel.send(f'Group with {str(group[1])} has been disbanded.')
                    await message.channel.send(f'Group with {str(group[0])} has been put back into the queue.')
                    matching_groups.append(group[0])
                    matched_groups.remove(group)
            await check_matching(message)
            write_file()
    elif message.content[0:7] == '!groups':
        if not matching_groups and not matched_groups:
            await message.channel.send(f'No groups formed currently.')
        for items in matching_groups:
            await message.channel.send(f'Group with {str(items)} is in queue.')
        for items in matched_groups:
            await message.channel.send(f'Group with {str(items[0])} is partnered with'
                                       f' group with {str(items[1])}.')
    elif message.content[0:12] == '!findpartner':
        if message.author in partners:
            await message.channel.send(f"You're already looking for a partner.")
        else:
            partners.append(message.author)
            await partner_matching(message)
    elif message.content[0:6] == '!clear':
        if message.author.guild_permissions.administrator:
            await message.channel.send(f"Cleared all groups.")
            matching_groups.clear()
            matched_groups.clear()
            write_file()
        else:
            await message.channel.send(f"You don't have the permissions for that.")
    elif message.content[0:9] == '!commands':
        await message.channel.send(f"**Commands**:\n"
                                   f"**!partner @member**: create a group with you and your partner, and mark yourselves as ready to start the PAR process with another group.\n"
                                   f"**!individual**: mark yourself as an individual and ready to start the PAR process with another group.\n"
                                   f"**!disband**: disband your current group, and remove yourself from queue, or if you are already paired, remove yourself from the pair.\n"
                                   f"**!groups**: show the current groups.\n"
                                   f"**!findpartner**: *before* you start working on your worksheet, use this command to find another individual that wants to work with someone.\n"
                                   f"**!clear**: clear groups, need administrator permission\n"
                                   f"**!commands**: list commands\n")



client.run(TOKEN)
