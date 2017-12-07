import time
import sys
from subprocess import call
from steem import Steem
from steem.post import Post
from steem.account import Account
from steem.converter import Converter
from steembase.exceptions import PostDoesNotExist

# *** Input steemit account to be used ***
# *** The account's posting key need to exist in your Steempy wallet ***
botname = 'STEEMIT-ACCOUNT'

steem = Steem()
bot = Account(botname)

# Used for conversion of steemit timestamp
pattern = '%Y-%m-%dT%H:%M:%S'

# Main function
def countervote(post):
    total = 0
    # Loop through all votes
    for vote in post.active_votes:
        # Check if the bot already voted
        if(vote['voter'] == botname):
            print('Already voted on this post.')
            total = 0
            break
        # Calculate the value of the flag and store it
        if(vote['percent'] < 0):
            user = Account(vote['voter'])
            flagValue = round(getrsharesvalue(vote['rshares']),4)
            print(vote['voter'] + ' downvoted the post with: $ ' + str(flagValue))
            total += flagValue

    # If there are flags, calculate the counter vote
    if(total < 0):
        print('Total downvoted value: $ ' + str(total) + '\n')
        VP = getactiveVP(bot)
        SP = calculateSP(bot)
        VW = round(getvoteweight(SP, abs(total), VP),4)
        # Make sure the vote weight is max 100
        if(VW > 100):
            VW = 100
        print('Voting with ' + str(VW) + '% to try to counter the vote.')
        counterValue = round(getvotevalue(SP, VP, VW),4)
        print('Counter vote value comes to: $ ' + str(counterValue))

        # Perform the vote
        t = call(["steempy", "upvote", "--account", botname, "--weight", str(VW), str(url)])
        if(t == 0):
            print('Successfully voted!')
        else:
            print('Failed to vote!!')


# Get the current upvote value based on rshares
def getrsharesvalue(rshares):
    conv = Converter()
    rew_bal = float(steem.steemd.get_reward_fund()['reward_balance'].rstrip(' STEEM'))
    rec_claim = float(steem.steemd.get_reward_fund()['recent_claims'])
    steemvalue = rshares * rew_bal / rec_claim
    return conv.steem_to_sbd(steemvalue)

# Calculates the total SP
def calculateSP(account):
    allSP = float(account.get('vesting_shares').rstrip(' VESTS'))
    delSP = float(account.get('delegated_vesting_shares').rstrip(' VESTS'))
    recSP = float(account.get('received_vesting_shares').rstrip(' VESTS'))
    activeSP = account.converter.vests_to_sp(allSP - delSP + recSP)
    return activeSP

# Calculates the active voting power
def getactiveVP(account):
    for event in account.get_account_history(-1,1000,filter_by='vote'):
        if(event['type'] == "vote"):
            if(event['voter'] == account.name):
                epochlastvote = int(time.mktime(time.strptime(event['timestamp'], pattern)))
                break
    timesincevote = int(time.time()) - epochlastvote
    VP = account.voting_power() + ((int(time.time())-epochlastvote) * (2000/86400)) / 100
    # Make sure the voting power is max 100
    if(VP > 100):
        VP = 100
    return VP

# Calculates the value of a vote
def getvotevalue(SP, VotingPower, VotingWeight):
    POWER = SP / (float(steem.steemd.get_dynamic_global_properties()['total_vesting_fund_steem'].rstrip(' STEEM')) \
        / float(steem.steemd.get_dynamic_global_properties()['total_vesting_shares'].rstrip(' VESTS')))
    VOTING = ((100 * VotingPower * (100 * VotingWeight) / 10000) + 49) / 50
    REW = float(steem.steemd.get_reward_fund()['reward_balance'].rstrip(' STEEM')) \
        / float(steem.steemd.get_reward_fund()['recent_claims'])
    PRICE = float(steem.steemd.get_current_median_history_price()['base'].rstrip(' SBD')) \
        / float(steem.steemd.get_current_median_history_price()['quote'].rstrip(' STEEM'))
    VoteValue = (POWER * VOTING * 100) * REW * PRICE
    return VoteValue

# Calculates the voting weight
def getvoteweight(SP, VoteValue, VotingPower):
    POWER = SP / (float(steem.steemd.get_dynamic_global_properties()['total_vesting_fund_steem'].rstrip(' STEEM')) \
        / float(steem.steemd.get_dynamic_global_properties()['total_vesting_shares'].rstrip(' VESTS')))
    REW = float(steem.steemd.get_reward_fund()['reward_balance'].rstrip(' STEEM')) \
        / float(steem.steemd.get_reward_fund()['recent_claims'])
    PRICE = float(steem.steemd.get_current_median_history_price()['base'].rstrip(' SBD')) \
        / float(steem.steemd.get_current_median_history_price()['quote'].rstrip(' STEEM'))
    VOTING = VoteValue / (POWER * 100 * REW * PRICE)
    VotingWeight = ((VOTING * 50 - 49) * 10000) / (100 * 100 * VotingPower)
    return VotingWeight

# Check for a valid Steemit URL and call the main function countervote()
try:
    url = sys.argv[1]
    post = Post(url)
except IndexError:
    print('Please input a Steemit URL')
except ValueError:
    print('Please input a Steemit URL')
except PostDoesNotExist:
    print('That is not a valid Steemit URL')
else:
    countervote(post)
