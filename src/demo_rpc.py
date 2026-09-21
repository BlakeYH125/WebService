from rpc_client import RPCClient

client = RPCClient()

print("1. create_profile:", client.create_profile())
print("2. get_profiles:", client.get_profiles())
print("3. get_profile:", client.get_profile(1))
print("4. update_profile:", client.update_profile(1, 1750000000))
print("5. create_query:", client.create_query(
    "python", 1, "test", "new"))
print("6. get_queries:", client.get_queries())
print("7. get_query:", client.get_query(1))
print("8. update_query:", client.update_query(
    1, description="updated", status="done"))
print("9. create_feedback:", client.create_feedback(
    "result", "error", "TimeoutError", 1))
print("10. get_feedbacks:", client.get_feedbacks())
print("11. get_feedback:", client.get_feedback(1))
print("12. update_feedback:", client.update_feedback(
    1, response="fixed", status="done", exception="None"))
print("13. get_recent_exceptions:", client.get_recent_exceptions())
