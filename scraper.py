import os


if not os.path.exists("data"):
    os.makedirs("data")

# We are creating a "Mock" database of 4 critical sections of Indian Tax Law.
# In the real world, this text comes from your web spider.

laws = {
    "Section_10_13A_HRA.txt": """
    SECTION 10(13A): HOUSE RENT ALLOWANCE (HRA)
    (1) Any special allowance specifically granted to an assessee by his employer to meet expenditure actually incurred on payment of rent 
    in respect of residential accommodation occupied by him, is exempt from tax to the extent of the least of the following:
    (a) Actual HRA received;
    (b) Rent paid in excess of 10% of salary;
    (c) 50% of salary (for metro cities) or 40% (for non-metro).
    """,
    
    "Section_24_Home_Loan.txt": """
    SECTION 24: DEDUCTIONS FROM INCOME FROM HOUSE PROPERTY
    Income chargeable under the head "Income from house property" shall be computed after making the following deductions, namely:—
    (a) a sum equal to thirty per cent of the annual value;
    (b) where the property has been acquired, constructed, repaired, renewed or reconstructed with borrowed capital, the amount of any interest payable on such capital.
    Provided that in respect of self-occupied property, the maximum deduction for interest on borrowed capital shall be 2,00,000 rupees.
    """,

    "Section_80D_Health_Insurance.txt": """
    SECTION 80D: DEDUCTION IN RESPECT OF HEALTH INSURANCE PREMIA
    (1) In computing the total income of an assessee, there shall be deducted the whole of the amount paid to keep in force an insurance on the health of the assessee or his family.
    (2) The aggregate of the sum referred to in sub-section (1) shall not exceed:
    (a) 25,000 rupees for oneself, spouse, and dependent children;
    (b) 50,000 rupees if the person specified is a senior citizen (above 60 years).
    """,
    
    "Section_80C_Investments.txt": """
    SECTION 80C: DEDUCTIONS FOR INVESTMENTS
    The total deduction available under this section is limited to 1,50,000 rupees per annum.
    Eligible investments include:
    - Life Insurance Premium (LIC)
    - Public Provident Fund (PPF)
    - Employees' Provident Fund (EPF)
    - Equity Linked Savings Scheme (ELSS)
    - Principal repayment of housing loan.
    """
}

def generate_library():
    print("Building Legal Library...")
    for filename, text in laws.items():
        path = os.path.join("data", filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.strip())
        print(f"-> Indexed: {filename}")
    print("Library construction complete.")

if __name__ == "__main__":
    generate_library()