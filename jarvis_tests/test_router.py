from ai.router import AIRouter

router = AIRouter()

response = router.route(

    "Open Chrome and then open YouTube"

)

print()

print("=" * 60)

for action in response.actions:

    print(action)

print("=" * 60)