from app.operator import run_lead_brief_operator

def main():
    print("Lead Brief Operator Ready.")
    print("Paste a company URL or type q to quit.")

    while True:
        user_input = input("\nURL: ").strip()

        if user_input.lower() in {"q", "quit", "exit"}:
            break

        result = run_lead_brief_operator(user_input)

        print("\n--- OPERATOR ---")
        print(result["message"])

        formatter = result["data"].get("formatter")
        if formatter and formatter["status"] == "ok":
            print("\n" + formatter["data"]["final_output"])
        else:
            print("\nNo final formatted output available.")

main()