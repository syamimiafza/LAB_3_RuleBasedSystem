import json
from typing import List, Dict, Any, Tuple
import operator
import streamlit as st

OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}

SCHOLARSHIP_RULES: List[Dict[str, Any]] = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0]
        ],
        "action": {
            "decision": "AWARD FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need"
        },
    },
    {
        "name": "Low CGPA not eligible",
        "priority": 95,
        "conditions": [
            ["cgpa", "<", 2.5]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement"
        },
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [
            ["disciplinary_actions", ">=", 2]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records"
        },
    },
    {
        "name": "Good candidate partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1]
        ],
        "action": {
            "decision": "AWARD PARTIAL",
            "reason": "Good academic & involvement record with moderate need"
        },
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000]
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score"
        },
    },
  
    {
        "name": "Default non-qualifier",
        "priority": 1,
        "conditions": [],
        "action": {
            "decision": "NOT ELIGIBLE",
            "reason": "Applicant did not meet the criteria for any defined scholarship or review."
        },
    }
]

def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    """Evaluate a single condition: [field, op, value]."""
    if len(cond) != 3:
        return False 
        
    field, op, value = cond
    
    if field not in facts or op not in OPS:
        return False
        
    try:
        return OPS[op](facts[field], value)
    except Exception as e:
        print(f"Error evaluating condition {cond} with fact {facts.get(field)}: {e}")
        return False

def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """Checks if all conditions in a rule are true (AND logic)."""
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))

def run_rules(facts: Dict[str, Any], rules: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Executes rules, returning the best action (highest priority) and all fired rules.
    """
    # Find all rules that match the current applicant facts
    fired = [r for r in rules if rule_matches(facts, r)]
    
    # If no rules fired, return a default review action
    if not fired:
        return ({"decision": "MANUAL REVIEW", "reason": "No specific rule matched (check rule configurations)"}, [])

    # Sort fired rules by priority (highest first)
    fired_sorted = sorted(fired, key=lambda r: r.get("priority", 0), reverse=True)
    
    best_action = fired_sorted[0].get("action", {"decision": "REVIEW", "reason": "Matching rule has no defined action"})
    
    return best_action, fired_sorted

st.set_page_config(page_title="Scholarship Advisory Rule System", page_icon="🎓", layout="wide")
st.title("🎓 University Scholarship Decision Support Tool")
st.caption("Enter applicant details and evaluate eligibility based on the configured rule set.")

with st.sidebar:
    st.header("Applicant Profile")
    st.subheader("Input Facts")

    input_cgpa = st.slider("1. Cumulative GPA (CGPA)", min_value=1.0, max_value=4.0, value=3.5, step=0.01)
    input_income = st.number_input("2. Monthly Family Income (RM)", min_value=0, max_value=20000, value=5000, step=100)
    input_score = st.slider("3. Co-curricular Involvement Score (0-100)", min_value=0, max_value=100, value=75, step=1)
    input_disciplinary = st.slider("4. Disciplinary Actions on Record", min_value=0, max_value=5, value=0, step=1)

    facts = {
        "cgpa": float(input_cgpa),
        "family_income": float(input_income),
        "co_curricular score": int(input_score),
        "disciplinary_actions": int(input_disciplinary),
    }

    st.divider()
    st.header("Rules Configuration")
    st.caption("You can edit the rules in JSON format below. Ensure the structure is valid.")
    
    default_json = json.dumps(SCHOLARSHIP_RULES, indent=2)
    rules_text = st.text_area("Edit rules here (JSON Array)", value=default_json, height=450)

    run = st.button("Evaluate Scholarship Eligibility", type="primary")

st.subheader("Applicant Facts for Evaluation")
st.json(facts)

try:
    rules = json.loads(rules_text)
    assert isinstance(rules, list), "Rules must be a JSON array"
except Exception as e:
    st.error(f"⚠️ Invalid rules JSON. Using the mandatory default rules. Error: {e}")
    rules = SCHOLARSHIP_RULES

st.subheader("Active Rule Set")
with st.expander("Show/Hide JSON Rule Configuration"):
    st.code(json.dumps(rules, indent=2), language="json")

st.divider()

if run:
    action, fired = run_rules(facts, rules)

    st.header("Decision Output")
    
    # Display the final decision based on the highest priority rule
    badge = action.get("decision", "REVIEW")
    reason = action.get("reason", "No reason provided.")

    if badge == "AWARD FULL":
        st.balloons()
        st.success(f"**FULL SCHOLARSHIP RECOMMENDED**")
        st.subheader(f"Decision: {badge}")
        st.markdown(f"**Reason:** *{reason}*")
        
    elif badge == "AWARD PARTIAL":
        st.success(f"**PARTIAL SCHOLARSHIP RECOMMENDED**")
        st.subheader(f"Decision: {badge}")
        st.markdown(f"**Reason:** *{reason}*")
        
    elif badge == "REJECT":
        st.error(f"**REJECTION RECOMMENDED**")
        st.subheader(f"Decision: {badge}")
        st.markdown(f"**Reason:** *{reason}*")
        
    else: # REVIEW, MANUAL REVIEW, NOT ELIGIBLE
        st.warning(f"**MANUAL REVIEW REQUIRED**")
        st.subheader(f"Decision: {badge}")
        st.markdown(f"**Reason:** *{reason}*")

    st.markdown("---")
    st.subheader("Fired Rules (Match History)")
    
    if not fired:
        st.info("No rules matched the applicant's profile.")
    else:
        st.markdown("The decision was based on the highest-priority rule from this list:")
        for i, r in enumerate(fired, start=1):
            
            # Highlight the highest priority rule
            if i == 1:
                st.markdown(f"### 🥇 **{r.get('name','(unnamed)')}** (Priority: {r.get('priority',0)})")
            else:
                st.markdown(f"#### {i}. {r.get('name','(unnamed)')} (Priority: {r.get('priority',0)})")
                
            st.markdown(f"Decision: `{r.get('action',{}).get('decision')}`")
            
            with st.expander("Show Conditions"):
                for cond in r.get("conditions", []):
                    st.code(f"Fact: {cond[0]} {cond[1]} {cond[2]}", language="python")
                    
else:
    st.info("Set applicant facts in the sidebar and click **Evaluate Scholarship Eligibility** to generate a decision.")