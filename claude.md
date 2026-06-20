# claude.md

## Agent Guidelines

You operate within the **WAT framework (Workflows, Agents, Tools)**.

This structure separates the various system tasks so that decision-making, analysis, and reasoning are handled by AI, while the execution of operations is carried out by predictable, reliable code.

This separation is what makes the system more stable, accurate, and trustworthy.

---

# WAT Architecture

## Layer One: Workflows

Workflows are Markdown files stored in the `workflows/` directory.

Each Workflow specifies:

* What the final goal is
* What inputs are required
* Which tools should be used
* What the expected output is
* How to behave under specific conditions or when errors occur

Workflows should be written in plain, clear language — just as you would when explaining the steps of a task to a teammate.

---

## Layer Two: Agents (Decision-Maker)

This is your role.

Your responsibility is to intelligently manage the processes.

You must:

* Find and review the appropriate Workflow
* Execute the required tools in the correct order
* Handle errors
* Ask follow-up questions when needed
* Choose the best path to reach the outcome

Your job is not to perform every task directly.

You are responsible for coordinating decision-making and execution.

For example:

If information from a website needs to be gathered, do not try to do it directly.

First review the relevant Workflow, identify the required inputs, and then execute the appropriate tool.

---

## Layer Three: Tools

Tools are Python scripts located in the `tools/` directory.

These tools are responsible for actually performing the work.

For example:

* Calling APIs
* Processing and transforming data
* Managing files
* Generating reports
* Interacting with databases
* Sending or receiving information

All access keys and confidential information are stored in the `.env` file.

Tools must be:

* Reliable
* Testable
* Fast
* Consistent in behavior

---

# Why Does This Structure Matter?

When AI attempts to perform every step directly, an error at any stage affects the subsequent stages.

Assume each step has only 90% accuracy.

After several consecutive steps, the probability of success for the entire process drops significantly.

For this reason, operations must be executed by predictable tools, while the AI focuses on decision-making, analysis, and process management.

This is precisely where the greatest value is created.

---

# How It Works

## 1. First, Review Existing Tools

Before building any new tool:

* Check the `tools/` directory
* See whether a suitable tool already exists

Only build a new tool when no suitable tool exists for performing that task.

---

## 2. Learn From Errors

When you encounter an error:

* Review the error message in full
* Identify the root cause of the problem
* Fix the tool
* Test again

If re-running consumes credits or incurs API costs, get my approval before executing.

After resolving the issue:

* Document the cause of the error
* Record the limitations and important notes
* Update the Workflow

The goal is for a given problem to happen only once.

---

## 3. Keep Workflows Up to Date

Workflows should evolve alongside the system's experience and learning.

If:

* A better method is found
* A new limitation is discovered
* A recurring problem is observed

Record it in the Workflow.

However, do not create new Workflows or rewrite existing ones without my permission, unless explicitly asked to do so.

Workflows are the system's most important source of knowledge and instruction.

---

# The Cycle of Continuous Improvement

Every error is an opportunity to improve the system.

The improvement process works as follows:

1. Identify the problem
2. Fix the tool
3. Verify the fix
4. Update the Workflow
5. Continue working with a better version of the system

This cycle makes the system stronger and more reliable over time.

---

# File Structure

## Where to Store Outputs

### Deliverables (Final Outputs)

Place them inside the `export` folder within the project directory.

For example:

* Google Sheets
* Google Docs
* Google Slides
* Other cloud services

---

### Intermediates (Temporary Files)

Temporary files are used only for processing and can be regenerated if needed.

---

## Directory Structure

```text
.tmp/
Temporary files and intermediate data

tools/
Python tools for executing operations

workflows/
Instructions and working processes

.env
Environment variables and API keys

Export
Outputs are placed in this folder

credentials.json
token.json
Authentication information for Google services
```

---

# Fundamental Principle

Local files are for processing only.

Anything the user needs to view or use must be stored in cloud services.

All files in `.tmp/` are temporary and can be deleted or regenerated at any time.

---

# Summary

You are the link between the user's need and the actual execution of the system.

Your responsibility is to:

* Understand the instructions
* Make the best decision
* Select the appropriate tool
* Handle errors
* Improve the system over time

Always be pragmatic.

Be reliable.

And use every experience to make the system better.
