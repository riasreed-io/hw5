# AI Prompts Log — Homework 5: Campus Customs Multi-Agent Operations

This file is the log of what I typed into my vibe coder (Claude Code) while
building this assignment. One section per problem, in the order I worked them.
Prompts are copied verbatim, typos and all.

**Session opener (before Problem 1):**

> im going to be doing this... take this information in. and im going to get
> started with the homework one prompt by one as the instructions state.

(Attached the assignment screenshots and `data (3).zip`.)

---

## Problem 1 — Vibe Coder Prompts

**Prompt 1 (typed by me):**

> problem 1: vibe coder prompts
>
> Create AI_prompts.md at the start of the assingment and keep it updates as i
> work. this file is the log of what i types into my vibe coder
>
> put one section for each problem, easch section must include:
>
> * the problem numnber and title
> * atleast one prompt i typed, in my own words as much as pssible
> * one filloe up prompt if i needed it (and one esnetece on what was lacking
>   after the first)

**Follow-up prompt:** none needed. The first prompt specified the file name,
the location, and the required contents of each section, so the log was created
correctly on the first pass.

---

## Problem 2 — Study the Campus Customs Database

**Prompt 1 (typed by me):**

> problem 2: study the campus customs database
>
> open data/campus_customs.db and look through every table and its fields. copy
> the oroginal file to data/campus_customs_new.db - later problems update that
> working copy
>
> study the three open tickets os i see how they link to other tables
>
> start output/harness.md.  and for each table, lsit the fields an one short
> line on why that table matters of the agents
>
> i will keep growing this harness file in later problems.
>
> for anything like this, show me the fields opeitons and why they might matter
> and then ill choose if needed

**Follow-up prompt:** none needed so far. The prompt named the source file, the
working copy, the output file, and the per-table format, so nothing was
ambiguous enough to require a second pass.

---

## Problem 3 — Build the MCP Server

**Prompt 1 (typed by me):**

> problem 3: build the mcp server
>
> write an MCP server in the mcp_server/ using FastMCP. it iwll talk to
> data/campus_customs_new.db. i do not need to connect or run it in this
> problem.
>
> Every agent in this homework uses the tools in this MCP server. i will add
> more tools to it later, for now write three tools i know i need for the
> tickets in the database. keep the names clear, never invent any data, only
> use the information in the database (first give me the options then i will
> choose)
>
> in output/harness.md , list each of hte three MCP tools. for every tool
> include: which table it reads, which teicket it helps unlock (101, 102, or
> 103) and one snetnece on wht that tool si the right one for that ticket
> (again, give me the options, and whyh it might matter, and then let me choose
> so i can write my one sentence each)
>
> vague lines like "reads inventory" score low - tie th etool to the ticket
>
> Also add a short mcp_server/README.md file that explains what the MCP server
> is for, which database files it uses, and the three tools it has.

**Follow-up prompt 1 (typed by me):**

> i feel like i needed to do this in my own words right? so i need to see the
> options, why they might be relevant, and then choose on my own and write in.
> my own words as well , just briefly

**What was lacking after the first prompt:** the first pass handed me finished
sentences to pick from instead of just the angles, so the harness lines were not
in my own words.

**Follow-up prompt 2 (typed by me, the three sentences themselves):**

> for mcp tool 1. i think i like the size vs sku tool so that it makes sure
> these are separate completely and not mixed up at all
>
> for 2nd, i think i like rent agains the other claims so that it cant be
> claimed elswhere, i think thats helpful so that things dont get mixed up and
> go negative
>
> and for 3. i like the names the actual blocker tool so that we can didentify
> what the actual problem is and get to the bottom of resolving it sooner than
> later which is helpful for efficiency

**Tool choices (also mine, from the options I asked for):** `check_stock` for
tickets 101 and 103, `list_money_due` for 102, and — since check_stock covered
two tickets and freed a slot — `check_vendor_can_ship` for the third.

---

## Problem 4 — Add the MCP Server to the Vibe Coder and Test Each Tool

**Prompt 1 (typed by me):**

> problem 4: add the mcp server to vibe coder and test each tool
>
> in the vibe coder, add the MCP service to this project so the vibe coder can
> call the tools. save the connection JSON text in .mcp.json at the project
> root or however my vibe coder saves local MCP server lists
>
> with teh vibe coder connected test each of the 3 MCP tools, save the evidence
> in output/mcp_smoke.json
>
> for every tool include:
>
> * the prompyt i asked the vibe coder
> * the tool name
> * the tool output (must match values in the data/campus_customs_new.db)
>
> if tehre is somethign i need to do for this question/problem give me all the
> relevant information and i wll make decisions based on your suggestions or
> something like that

**Follow-up prompt (typed by me):**

> you cant just help me test the three test prompts?

**What was lacking after the first prompt:** the first pass set up the
connection but said the tools could not be tested until I restarted the app, so
the follow-up pushed for a way to run the three tests right away — which turned
out to be headless `claude -p` sessions loading the same `.mcp.json`.

**Decision I made from the options given:** register `campus-customs` in the
monorepo root `.mcp.json` as well as in `homework 5/.mcp.json`, rather than
starting a separate session in the homework folder and losing the context from
Problems 1–3.


---

## Problem 5 — Build the Agent Team and Grow the MCP Tools

**Prompt 1 (typed by me):**

> problem 5: buidl the agent team and grow the MCP tools
>
> build the agenetic team for campus customs using pydanticAIL boss: inventory,
> Accounting, Facilities, Customerserives. including prompts, models, and agent
> loops so they can delegate work to each other with full connectivity
>
> put the anget promts in backend/prompts/ - one file per agent. put data types
> in backend/models.py, and agent files under backend/ (your layout can vary as
> long as the five roles are clear. use the portkey_api_key and only gpt-6-luna
> for every agent (or claude equiavalent).
>
> Write each prompt in my own words with teh ship rule shta tgent needs more
> detialed prmpts that cover all aspects of an agents work and scopr sorre
> higher than a short generic prompt
>
> add any tool the agnets need to your MCP service so they can work on the open
> tickets. shop facts come from the MCP server over data/campus_customs_new.db
> - do not invent a second shop-tools later that bypasses MCP
>
> wire teh agnets so they append to output/audit_trail.json as they run: for
> each eagent-loop step, record enough to audit later. append to this file - do
> not wipe it each run
>
> in output/harness.md, list each agent and each MCP tool (including ones you
> add in this problem) along with which table the tool uses. also add ashort
> safety section: the guardrails a real business would want when agents touch
> real customers and real money, plus the limits that keep tojen use in check
>
> update mcp_server/README.md so the tool list mateches what i ahve now
>
> BEFORE DOING ANYT OF THIS, tell me what the question is asking of me, give me
> the options of what i can consider, what i might think abotu in this
> coniserdetion, and then il lrespond. number the different things the question
> wants me to answer and run me thorugh it. once i complete these inputs, then
> do the problem with my inputs

**Follow-up prompts (typed by me):** three rounds pushing for a clearer
decision brief — "you have to differenetiate what its asking me vs what its
asking you", "ultra ultra ultra concise", and "i need to know whats being
asked, what the posible answers are, and then ill answer them".

**What was lacking after the first prompt:** the first pass mixed my decisions
together with the vibe coder's build work and offered curated defaults instead
of the full option space, so I could not tell which choices were actually mine
to make.

**My answers (typed by me):**

> 1. lets add the open tickets one where the boss can act efficiently when
> working with tickets, that will be helpful in managing them, lets also add
> the approve and pay tool where the money moves with the right conditions in
> mind, and lets do and and update inventory so that the restock can be
> properly managed ans well as the information in palce for agents and boss to
> navigate
>
> 2. i liek the two step option where the pending reord and a seprerate approve
> and pay is the only thign tha tmoves cash so that there is no chance that
> money moves without explicit approval like the prompt wants
>
> 3. you handle this
> 4. this is what you handle too
> 5. you also do this
> 6. i dont undersatnd so this is liely in your field of whats being asked for
> oyu to do
>
> 7. boss does the managing, and reads ervery ticket but me as the human can
> override and i also speak with the boss only not the other agents, for
> inventory they look at the all the things reltaed to inventory like size
> restock and it can also handle things like lead times if it is related to
> inventory, for accounting it needs to do what the boss asks but keep
> accounting principles in tact and doesnt make decisions tha tthe boss hsould
> make, for facilities it is stuff like rent before bendor bills on princeple,
> ticket to closing reporting to boss, and customer service to tell the
> customer and be warm and customer facing and can only promise things only
> iwth bosses approval
>
> 8. youre doing that

**What I decided vs what the vibe coder decided:** the five role definitions in
answer 7 are mine and are quoted at the top of each prompt file. The tool set,
the two-step approval gate, and the choice to give `approve_and_pay` to nobody
are mine. Delegation mechanics, token ceilings, audit format, the shop policy
values, and all code were the vibe coder's, per my answers 3-6 and 8.

---

## Problem 6 — Plan the Three Tickets

**Prompt 1 (typed by me):**

> problem 6: plan the three tickets
>
> before i wirte the backend, write down that i expect the team to do on each
> open ticket. build output/desk_tickets.html - a page i can double ckick with
> one tab per ticket (101,102,103) also add empty cash and reflection tabs for
> later problems (leave them blank or wwith a short coming later note for now
>
> on each ticket tab, fill an expected section only (leave room for an actual
> section i need to fill after i run th agents)
>
> for each tickets expected section write in my own words:
>
> * who the boss hsould call first and why
> * all the agnets delegations i expect - not the boss calls everyone
> * which MCP tools i expect that run to use
>
> plan and send every specialist on every ticket score low. i will compare this
> plan to what actually happens when the agent resolves the three tickets
>
> so for what it is asking, i think it wil llielly be the boss who calls on the
> agents but there might stull be som abgibutiies that exist or some issues as
> to who needs to be called on or ways that things can be more efficient. but
> those will get worked on if the agents can train on their past efficienties.
> i think when opening the ticket, all agents will be called only when a few
> need to be called at a time
>
> for the rest of the expected secction, give me each ticket and possible
> considerations so that i can answer each of those with informed answers, so
> liek before give me the information, context, etc so that ican answer with
> all necessary information

**Follow-up prompt (my expectations, typed by me):**

> for 101, i think it will call on accounting first becuase it needs to be paid
> to be executed and also inventory becuase to make sure the right size is in
> stock, and i think mcp tools are similar to the inventory, and the pay
> features tools
>
> for 102, i thin facilities shoudl be called first becuas ethis invoves rent,
> i do think accouting shoudl also be called becuase it involves money, and the
> MCP tools might eb related to request payment, or list money due type of
> tools
>
> For 103, i think inventory gets called first because it needs to be in stock
> for it to go any furhter, but also accounting is needed because it needs to
> be resolved with financials, and i tihnk similar MCP tools will get called
> like inventory related ones and the ones as it relates to list payment
> requests as well

**What was lacking after the first prompt:** nothing was missing — the first
prompt asked for the per-ticket facts first so the expectations would be
informed, and the follow-up is those expectations.

**Note on honesty of this plan:** a partial agent run had already happened
during Problem 5 before this plan was written. The vibe coder had the run's
audit trail and deliberately withheld what the agents actually did, so the
expected sections are written blind.

---

## Problem 7 — Backend Routes

**Prompt 1 (typed by me):**

> problem 7: backend routes
>
> your react frontend dashboard (the next problem) needs a backend it can call.
> in backend/main.py, use the FastAPI and add routes that do the following:
>
> * return the three tickets and whether each is open or resolved
> * Take a ticket id and run your agent team on taht ticket
> * Return recent agent events - what each agent said nwhic tools they used -
>   so the board can refresh
> * approve a payment or pruchase after a human clicks approve (agents only
>   prepare the pay, this route is what actually changes cash)
> * return the current checking balance from cash_accounts
> * reset the database to the original values when i want to try a fresh run
>
> from the backend/ folder, start the server with
> uvicorn main:app --reload --port 8000
>
> this turns on the backend at http://localhost:8000 so tehe frontend dashbaord
> can call those routes
>
> in output/harness.md, list each route in one line (what URL / what i does).

**Follow-up prompt:** none needed. The six routes were specified clearly enough
to build and test in one pass.

**Note:** port 8000 was already occupied by the Homework 4 backend still
running in the background, so the routes were verified by driving the ASGI app
directly rather than over the port.

---

## Problem 8 — Agent Dashboard

**Prompt 1 (typed by me):**

> problem 8: agent dashboard
>
> build a frontend dashboard in frontend/ with react + vite + typescript. the
> page should call the routes you built in problem 7. at minimum the baord
> should:
>
> * list all three tickets
> * let me pick one ticket and start eh agent team on it
> * show each agent and waht they are saying / doing while the ticket runs
> * mark the ticket resolve when the run finishes
> * show a short summary of what each agent did on that ticket
> * let a human approve a pay or purchase when asked
> * shwow the checking balance (it should drop after an approved pay)
>
> make a dashboard look good, be vreateive with teh layout and feel - this is
> a real desk people would wnat to sit at, so put thought into how it looks
>
> i want this to look super professional and modern, maybe even slightly
> futuristic,, minialistic and sleek kind of like apple's kind of vibe and
> design, i also like the liquid glass they are using which makes thigns look
> liek youre looking through glass objects but its digital
>
> tell the forn tend to talk to the backend at http://localhost:8000. on the
> backend, allow the vite page origin (usually http://localhost:5173) so the
> browser is allowed to call those routes.
>
> start eh board with : npm run dev
>
> this oepens the react desk in my browswer so i can pick the tickets and
> watch the agents
>
> Write output/design.md with ath i chose fo rthe dhasboar dlook (layout, how
> agents read differently, how resolved tickets and cash show up, and why,
> including the ceateive choicses that make it feel special and somethign
> humans would actually enjoy using
>
> so i want this to be apple inspiried. we can lso lean into the apple theme
> and use actual apples for the differnet agents, making each one a differnt
> apple, and i think it should be visually interesting too in taht they animate
> while thhey are working and text bubbles come up to but with this liquid
> glass tpy eof thing, alwasy remember to keep thigns ssleek, and design
> forward so it reminds the user of an apple type od aesthetic, and it can even
> be 2D which can be stylish rather than a cheesy 3D thing

**Follow-up prompt:** none needed. The design direction — Apple-inspired,
liquid glass, one apple variety per agent, animated, 2D not 3D — was specific
enough to build from in one pass.

**My design decisions:** apples as the agent characters, one variety each;
liquid glass surfaces; 2D over 3D; animation while working. Written up in
`output/design.md`.

---

## Problem 9 — Clean Run, Cash Reconciliation, and Artifacts

**Prompt 1 (typed by me):**

> before testing the agents on a full run over the three tickets, reset the
> working database data/campus_customs_new.db again so you can start clean.
> note the starting checking balance, then run all the three tickets on teh
> board (101, 102, and 103)) until each is resolved
>
> open output/desk_tickets.html from problem 6. on each ticket tab, fill the
> actual section from this run: which agents worked, what they delegated and
> which tolls they sued. leep my expected section so i can compare the two
>
> (help me do this comparison, show me what i need so i can canswer this
> accuratley
>
> on the cash tab of the same output/desk_tickets.html, itemize the money:
>
> * starting checking balance (after the reset)
> * for each ticketL how cash changed when that ticket resolved, and why
>   (which pay / purchse, dollar amount)
> * ending checking balance - it must match cash_accounts in teh working
>   database
>
> wrong cash math loses points even if the board shows every ticket is resolved
>
> also save:
>
> * output/resolved_tickets.json - for each ticket: id, final status, short
>   outcome, what each agent contributed, and any human approvlas
> * output/resolved_board.html - a page i can double click with a scnreenshot
>   of my react board for each resolved ticket
>
> append real runs to output/audit_trail.json. finish output/harness.md so it
> covers table,s MCP tools, the five agents, API routes, teh dashboard, and
> safety rules.

**Follow-up prompt:** none needed.

**What happened that I had to decide:** ticket 101 would not resolve on two
separate passes. The Boss prompt I wrote said never to close a ticket whose
work is not done, and the reprinted tee does not arrive until 2026-09-05, so
the Boss correctly kept it open. The prompt was amended to allow closing a
ticket when the only remaining step is outside the shop's hands — a vendor's
lead time, a human approval, a customer reply — with the outstanding item
written into the resolution. Pass 3 then resolved it. The original prompt is
backed up and the change is recorded in the Actual section of ticket 101.

**Follow-up prompt (my reflection, typed by me):**

> for 101, i got it mostly right, but the order of it was differnet so it did
> call on customer service afterall so tht was wrong with my prediciton
>
> for 102, the tools i predicted did actualy get use,d bit i ws wrong about
> facilities being called on which was overlooked by me initially
>
> for 103, i got the right agents and inventory tools but i did miss the order
> and customer serivce being called altogethr as well as the list payment
> requests tool so that was also miscalcualted on my end for the prediciton
>
> it did surpuse me how well it actually ran with its own, it is quite
> proficient, i think the boss skipped a few things bcexuse its still learnign
> though, i would change the prompts to be more systematic about how its going
> to decide on calling agents basically so that the strcuture is quite clear so
> that there isnt some guessing and especially no mistakes, i think the token
> usage is okay for a first few runs, it will get more effiicent over time

**Follow-up prompt (my safety priorities, typed by me):**

> i think approved by is good becuase it can tehn trace that it was calimed by
> a person, it should never be approved by AI, and no agent holds approved and
> pay so that it isnt posible for them to approve
>
> and i like request payment checsk the amount owed so it cant make up figures

**Where my words landed:** the Reflection tab of `output/desk_tickets.html` and
the top of the safety section in `output/harness.md`. Typos were corrected;
nothing was reworded.

---

## Problem 10 — Reflection

**Prompt 1 (typed by me, with my answers inline):**

> problem 10: reflection
>
> open output/desk_tickets.html and fill the reflection tab. answer in my own
> vibe and detailed and thorough:
>
> how woudl i evelaute the performance of the agents on each ticket
>
> * they would have to be accurate, and effieicent, and does so in only calling
>   the right agents, and it has to be super super accurate on the financials
>   and quick to answer is how id evaluate, it also has to address the
>   specifics fo the ticket, all aspects of ti
>
> for each ticket, how did actual compare to the expted plan i wrote earlier
>
> * fill in my answer here from i already wrote, which i answered this earlier
>
> what would ahve been simpler as one agent with tools - and why?
>
> * i think it wouldve been simpler with some tasks and a full range of tasks,
>   some of these tickets arent all that complex so it seems like it could be
>   handled by one agent though
>
> describe three new problems campus customs might face that htis agnet team
> could solve with the tools i built
>
> * it seems like it could handle an order that is requesting an inquiry on
>   inventory for multiple orders and the tools can figure that out, i also
>   think it could handle an order that is asking for a quote for a bulk order,
>   and i think it could handle a customer serivce issue where they wanted a
>   certain size but then changed their mind and wanted to order a differnt
>   size before they placed the order
>
> describe three new problems the agent team cold not solve and explain the
> tolls and agents i would need ot solve them
>
> * they could not handle a refund, which would require new tools to process
>   the refund, check inventory to offer an alternatiave to the order that the
>   customer doesnt wnat anymore, i also dont thin the tools can handle a wrong
>   roder which they return as well and i would need the same tools for the
>   refund and i think they would need tools to handle shipping return
>   refunding and apologizing, and i think they couldnt handle something where
>   they wanted to purchase or acquire the company which would require tools to
>   assess the companeis performance against their offer
>
> tie every answer to this app and the three tickets i ran - uset ht eicket
> tabs and cashtab on the same page as my evidnce, generic AI essays without
> cuampus customs details will score low

**Follow-up prompt:** none needed. I gave my position on all five questions in
the first prompt; the vibe coder's job was to attach the evidence from my own
ticket tabs and cash tab to each answer, not to supply opinions.

**How my answers were used:** every claim in the Reflection tab is one of my
five positions, expanded with figures from this run — 0 of 1 in size S, 8 of 20
in M, 3,400.00 → 2,560.00 → 160.00, 20,550 vs 69,725 vs 159,525 tokens,
Facilities asleep on all three tickets, `list_payment_requests` never called on
103. Nothing generic was added.
