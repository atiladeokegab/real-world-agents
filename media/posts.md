# Post drafts (post only after submit; figures from eval round 3b)

## LinkedIn

We built a bank operations agent at the Real-World Agents Hackathon (Dwelly, London), Banking track.

A customer asks about one payment. The batch says "processed". The agent does not take that at face value: plain code checks the evidence first, so a batch status is not mistaken for a row status.

What it does, in plain words:
- Checks the evidence in code before the model reasons over it.
- Takes authority from code, never from the model.
- Never moves money twice.
- When it should stop, hands over with a clear note a person can act on.

Every case ends with an answer, the reasoning, and a trace that shows why.

On our 50 practice cases: 84% of first actions match the bank's, and 9/10 judgement cases are handled safely.

Code: https://github.com/atiladeokegab/real-world-agents

#AIAgents #Banking #Hackathon

## X

Bank ops agent, Real-World Agents Hackathon (Dwelly, London), Banking track. Code checks the evidence, authority comes from code, money never moves twice, it hands over with a note. 84% first-action match on 50 practice cases. https://github.com/atiladeokegab/real-world-agents
