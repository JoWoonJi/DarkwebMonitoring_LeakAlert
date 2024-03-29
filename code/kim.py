import requests

token = 'xoxb-6828434958416-6863246448065-UjRczyKKN6Gwn5ic9Sb0h4i1'
channel = '#다크웹알리미'
text = 'check your leak info crawler'

requests.post('https://slack.com/api/chat.postMessage', 
              headers = {"Authorization": "Bearer "+token},
              data={"channel":channel,"text":text})