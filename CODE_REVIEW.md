# Code Review Guidelines

> **Instructions**: Customize this template for your team's code review process. This includes both automated (Claude Code) and manual review guidelines. Delete this block when done.

## Overview

**Review Philosophy**: [e.g., "Code review is about learning, improving quality, and sharing knowledge—not gatekeeping"]

**Review Goals**:
1. Catch bugs and errors before production
2. Ensure code quality and maintainability
3. Share knowledge across the team
4. Maintain consistency with standards
5. Improve security and performance

---

## Automated Reviews with Claude Code

### Setup Claude Code GitHub App

**Installation Steps**:

1. **In Claude Code CLI**:
   ```bash
   /install-github-app
   ```

2. **Follow the screens**:
   - Authorize GitHub access
   - Select repositories
   - Grant required permissions

3. **Verify Installation**:
   - Claude Code will add `CLAUDE_CODE_OAUTH_TOKEN` to repository secrets
   - GitHub workflow files will be created in `.github/workflows/`

4. **Configuration**:
   The GitHub App will automatically:
   - Review every pull request
   - Add comments on code quality issues
   - Check against CLAUDE.md principles
   - Flag security vulnerabilities
   - Suggest improvements

### What Claude Code Reviews

**Automatically Checks**:
- [ ] Code follows HOWTOCODE principles
- [ ] Tests are present for new functionality
- [ ] Linter passes (no warnings)
- [ ] Security vulnerabilities (SQL injection, XSS, etc.)
- [ ] Performance issues (N+1 queries, inefficient loops)
- [ ] Error handling is present
- [ ] No hardcoded secrets or credentials
- [ ] No commented-out code
- [ ] Imports are used
- [ ] Functions are reasonably sized (< 50 lines)

**Provides Suggestions For**:
- Better variable names
- Simpler implementations
- Edge cases to handle
- Missing tests
- Documentation improvements
- Accessibility issues

---

## Manual Code Review Process

### Before Requesting Review

**Author Checklist**:
- [ ] Code runs locally without errors
- [ ] All tests pass (`make test`)
- [ ] Linter passes (`make lint`)
- [ ] No debugging code (console.logs, debuggers)
- [ ] CLAUDE.md principles followed
- [ ] Tests added for new features
- [ ] Relevant documentation updated
- [ ] PR description is clear and complete
- [ ] Screenshots added (for UI changes)
- [ ] Database migrations tested (if applicable)

### PR Description Template

```markdown
## What changed?
[Brief description of changes]

## Why?
[Problem being solved or feature being added]

## How to test?
1. [Step-by-step testing instructions]
2. [Include test accounts, data setup if needed]

## Screenshots (if UI changes)
[Before/After screenshots]

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented if yes)
- [ ] Database migrations included (if needed)
- [ ] Reviewed my own code first
```

### Review Timeline

**Expected Response Times**:
- **Urgent/Hotfix**: 1-2 hours
- **Normal PR**: 24 hours
- **Large PR (500+ lines)**: 48 hours

**Author Responsibilities**:
- Respond to feedback within 24 hours
- Re-request review after addressing comments
- Merge promptly after approval

**Reviewer Responsibilities**:
- Review within expected timeline
- Provide constructive feedback
- Approve or request changes (don't leave in limbo)

---

## What to Review

### 1. Correctness

**Questions to Ask**:
- Does the code do what it's supposed to do?
- Are there edge cases not handled?
- Could this cause bugs in production?
- Are error cases handled properly?

**Red Flags**:
- ❌ No error handling
- ❌ Assumptions about data format
- ❌ Missing validation
- ❌ Race conditions or timing issues

### 2. Code Quality

**Questions to Ask**:
- Is the code readable and maintainable?
- Are variable/function names descriptive?
- Is the logic easy to follow?
- Could this be simpler?

**Red Flags**:
- ❌ Complex nested logic (> 3 levels)
- ❌ Functions > 50 lines
- ❌ Unclear variable names (`x`, `temp`, `data`)
- ❌ Duplicate code
- ❌ Comments explaining "what" instead of "why"

**Good Examples**:
```javascript
// ✅ GOOD: Descriptive names, clear logic
function calculateUserDiscount(user, orderTotal) {
  if (user.membershipTier === 'premium') {
    return orderTotal * 0.15
  }
  return 0
}

// ❌ BAD: Unclear names, magic numbers
function calc(u, t) {
  if (u.t === 'p') {
    return t * 0.15
  }
  return 0
}
```

### 3. Testing

**Questions to Ask**:
- Are there tests for new functionality?
- Do tests cover edge cases?
- Are tests readable and maintainable?
- Do all tests pass?

**Red Flags**:
- ❌ No tests for new features
- ❌ Tests only cover happy path
- ❌ Tests are brittle (implementation-dependent)
- ❌ Tests don't actually test anything

**Coverage Requirements**:
- New features: Must have tests
- Bug fixes: Must have regression test
- Refactoring: Existing tests should still pass
- Overall coverage: Must not decrease

### 4. Security

**Questions to Ask**:
- Could this introduce security vulnerabilities?
- Is user input validated and sanitized?
- Are secrets handled properly?
- Is authentication/authorization correct?

**Red Flags**:
- ❌ SQL injection risk (string concatenation)
- ❌ XSS vulnerability (unescaped user input)
- ❌ Hardcoded secrets or API keys
- ❌ Missing authentication checks
- ❌ Sensitive data logged
- ❌ CORS misconfiguration

**Examples**:
```javascript
// ❌ BAD: SQL injection risk
const query = `SELECT * FROM users WHERE id = ${userId}`

// ✅ GOOD: Parameterized query
const query = 'SELECT * FROM users WHERE id = ?'
db.query(query, [userId])

// ❌ BAD: XSS vulnerability
element.innerHTML = userInput

// ✅ GOOD: Escaped output
element.textContent = userInput
```

### 5. Performance

**Questions to Ask**:
- Could this cause performance issues?
- Are there N+1 query problems?
- Is pagination implemented for large datasets?
- Are expensive operations cached?

**Red Flags**:
- ❌ Database queries in loops
- ❌ No pagination for list endpoints
- ❌ Expensive calculations not cached
- ❌ Large files loaded into memory
- ❌ Synchronous operations blocking

**Examples**:
```javascript
// ❌ BAD: N+1 query problem
for (const user of users) {
  const posts = await db.query('SELECT * FROM posts WHERE user_id = ?', [user.id])
}

// ✅ GOOD: Single query with join
const usersWithPosts = await db.query(`
  SELECT users.*, posts.*
  FROM users
  LEFT JOIN posts ON posts.user_id = users.id
`)
```

### 6. Design and Architecture

**Questions to Ask**:
- Does this fit the existing architecture?
- Is this the right place for this code?
- Are there better patterns to use?
- Is this over-engineered or under-engineered?

**Red Flags**:
- ❌ Business logic in UI components
- ❌ Tight coupling between modules
- ❌ God objects/functions doing too much
- ❌ Premature abstraction
- ❌ Violates existing patterns

---

## How to Review Code

### Review Size Guidelines

**Ideal PR Size**:
- Small: < 100 lines (15 minutes)
- Medium: 100-300 lines (30 minutes)
- Large: 300-500 lines (1 hour)
- Too Large: > 500 lines (break it up!)

**For Large PRs**:
- Ask author to split into smaller PRs
- Review in multiple sessions
- Focus on high-risk areas first
- Consider pairing with author

### Review Workflow

**1. Understand Context** (5 minutes):
- Read PR description
- Understand the problem being solved
- Review linked issues/tickets
- Check related PRs

**2. High-Level Review** (10 minutes):
- Review file structure changes
- Check for architectural concerns
- Identify risky areas
- Verify tests are present

**3. Detailed Review** (30 minutes):
- Read code line by line
- Check logic and correctness
- Look for edge cases
- Review tests
- Check for security issues

**4. Test Locally** (15 minutes):
- Pull the branch
- Run the code locally
- Test the feature manually
- Run test suite

**5. Provide Feedback** (10 minutes):
- Write constructive comments
- Suggest improvements
- Approve or request changes

### Providing Feedback

**Types of Comments**:

**🔴 Blocking (must fix)**:
```
🔴 BLOCKING: This SQL injection vulnerability must be fixed before merging.

// Current code
const query = `SELECT * FROM users WHERE email = '${email}'`

// Suggested fix
const query = 'SELECT * FROM users WHERE email = ?'
db.query(query, [email])
```

**🟡 Important (should fix)**:
```
🟡 SUGGESTION: This N+1 query could cause performance issues with many users.
Consider using a join or batch loading instead.
```

**🟢 Nice-to-have (optional)**:
```
🟢 NIT: Consider renaming `data` to `userProfile` for clarity.
Not blocking, but would improve readability.
```

**💡 Learning (educational)**:
```
💡 TIL: Did you know you can use optional chaining here?

// Instead of
const name = user && user.profile && user.profile.name

// You can use
const name = user?.profile?.name
```

**Writing Constructive Comments**:

✅ **DO**:
- Be specific and actionable
- Explain the "why" behind feedback
- Suggest solutions, not just problems
- Praise good code
- Ask questions to understand intent

❌ **DON'T**:
- Be condescending or rude
- Nitpick formatting (let linters handle it)
- Bikeshed (argue over trivial preferences)
- Block PRs for style preferences
- Provide vague feedback

**Examples**:

```
❌ BAD: "This is wrong."

✅ GOOD: "This could cause a bug when `user` is null.
Consider adding a null check:
if (!user) return null
```

```
❌ BAD: "Why didn't you use async/await?"

✅ GOOD: "async/await would make this more readable. Here's how:
async function fetchData() {
  const response = await fetch(url)
  return response.json()
}
What do you think?"
```

---

## Review Checklist

### Pre-Review (Author)

- [ ] Self-reviewed my code
- [ ] Tests added and passing
- [ ] Linter passing
- [ ] No debugging code left
- [ ] PR description complete
- [ ] Screenshots added (UI changes)
- [ ] Documentation updated

### During Review (Reviewer)

**Correctness**:
- [ ] Code does what it's supposed to do
- [ ] Edge cases handled
- [ ] Error handling present
- [ ] No obvious bugs

**Quality**:
- [ ] Code is readable
- [ ] Functions are reasonably sized
- [ ] Variable names are descriptive
- [ ] No unnecessary complexity

**Testing**:
- [ ] Tests exist for new functionality
- [ ] Tests cover edge cases
- [ ] All tests pass
- [ ] Coverage hasn't decreased

**Security**:
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] User input validated
- [ ] No hardcoded secrets
- [ ] Auth/authz checks present

**Performance**:
- [ ] No N+1 query problems
- [ ] Pagination for large datasets
- [ ] No blocking operations
- [ ] Reasonable database queries

**Architecture**:
- [ ] Fits existing patterns
- [ ] No tight coupling
- [ ] Appropriate abstraction level
- [ ] Follows SOLID principles

### Post-Review (Both)

- [ ] All comments addressed or discussed
- [ ] CI/CD pipeline passes
- [ ] Claude Code review passed
- [ ] At least one human approval
- [ ] Author confirmed ready to merge

---

## Common Review Patterns

### Approving PRs

**When to Approve**:
- All blocking comments addressed
- Tests pass and coverage maintained
- No security vulnerabilities
- Follows code standards
- Ready to deploy

**Approval Comment Template**:
```
✅ LGTM! (Looks Good To Me)

Nice work on [specific positive feedback].

A few minor suggestions but nothing blocking:
- [Optional improvement 1]
- [Optional improvement 2]

Approved!
```

### Requesting Changes

**When to Request Changes**:
- Blocking issues found
- Security vulnerabilities
- Missing tests
- Breaks existing functionality
- Significant architectural concerns

**Request Changes Template**:
```
Thanks for the PR! I found a few issues that need addressing before we can merge:

🔴 BLOCKING:
1. [Critical issue 1]
2. [Critical issue 2]

🟡 IMPORTANT:
1. [Important but non-critical issue]

Please address these and I'll re-review. Happy to discuss any of these!
```

### Commenting Without Approving

**When to Use**:
- You're not the final approver
- You have questions but no blocking concerns
- You want to provide optional suggestions

**Comment Template**:
```
A few thoughts:

💡 Suggestions:
- [Suggestion 1]
- [Suggestion 2]

Questions:
- [Question about approach]

Not blocking, just wanted to share feedback. Will let [other reviewer] give final approval.
```

---

## PR Size and Scope

### Ideal PR Characteristics

**Good PR**:
- Solves one problem
- < 300 lines changed
- Has clear description
- Includes tests
- Can be reviewed in 30 minutes

**Bad PR**:
- Solves multiple unrelated problems
- > 500 lines changed
- Vague description
- No tests
- Takes hours to review

### Breaking Up Large PRs

**Strategies**:

1. **Separate Refactoring from Features**:
   - PR 1: Refactor existing code
   - PR 2: Add new feature using refactored code

2. **Layer by Layer**:
   - PR 1: Database schema changes
   - PR 2: Backend API
   - PR 3: Frontend UI

3. **Feature Flags**:
   - PR 1: Add feature (behind flag)
   - PR 2: Iterate on feature
   - PR 3: Enable feature flag

---

## Emergency Hotfix Process

### When to Use Hotfix Process

- Production is down
- Critical security vulnerability
- Data loss risk
- Severe user impact

### Hotfix Review Process

1. **Create hotfix branch** from `main`
2. **Fix the issue** (minimal changes only)
3. **Test locally** (verify fix works)
4. **Create PR** with `[HOTFIX]` label
5. **Fast-track review** (1-2 hours max)
6. **Merge and deploy** immediately
7. **Follow-up PR** with tests and proper fix

**Hotfix Review Checklist** (expedited):
- [ ] Fixes the critical issue
- [ ] No unrelated changes
- [ ] Tested locally
- [ ] Won't make things worse
- [ ] Follow-up PR planned

---

## Metrics and Monitoring

### Review Health Metrics

**Track**:
- Average time to first review
- Average time to merge
- Number of review iterations
- PR size distribution
- Review participation

**Target Metrics**:
- Time to first review: < 24 hours
- Time to merge: < 48 hours
- Review iterations: < 3
- PR size: 80% under 300 lines
- Review participation: > 80% of team

### Code Quality Metrics

**Track**:
- Test coverage trend
- Linter violations
- Claude Code review pass rate
- Security vulnerabilities found
- Production bugs linked to PRs

---

## Tools and Automation

### Required Tools

**Automated Checks**:
- [ ] Claude Code GitHub App (automated reviews)
- [ ] Linters (code style)
- [ ] Test suite (functionality)
- [ ] Security scanners (vulnerabilities)
- [ ] Code coverage (test completeness)

**CI/CD Integration**:
```yaml
# .github/workflows/pr-checks.yml
name: PR Checks

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run linter
        run: npm run lint
      - name: Run tests
        run: npm test
      - name: Check coverage
        run: npm run test:coverage
      - name: Security scan
        run: npm audit
```

### Recommended Tools

**Code Review**:
- GitHub PR interface
- Claude Code automated reviews
- Git blame for context

**Testing**:
- Local testing environment
- Preview deployments (Vercel, Render)
- Playwright for UI testing

**Documentation**:
- PR templates
- Code commenting
- ADRs (Architecture Decision Records)

---

## Training and Onboarding

### For New Reviewers

**Week 1-2**: Shadow Reviews
- Join review discussions
- Read comments from experienced reviewers
- Ask questions about decisions

**Week 3-4**: Co-Review
- Review PRs together with experienced reviewer
- Discuss findings before commenting
- Get feedback on review comments

**Week 5+**: Independent Review
- Review PRs independently
- Get feedback on review quality
- Gradually take on more responsibility

### For New Authors

**Resources**:
- Read CLAUDE.md
- Read this CODE_REVIEW.md
- Review example PRs
- Attend code review training

---

## FAQ

**Q: How do I disagree with a reviewer?**
A: Discuss in comments or synchronously (call/chat). Assume good intent. If still stuck, escalate to tech lead.

**Q: Can I merge if Claude Code flags issues?**
A: Only if a human reviewer confirms it's a false positive and approves.

**Q: What if reviews are taking too long?**
A: Tag reviewers, ping in Slack, ask in standup. For urgent PRs, label as `urgent`.

**Q: Should I approve if I don't understand the code?**
A: No. Ask questions until you understand. Or tag someone with more context.

**Q: What if I disagree with the approach entirely?**
A: Comment early. Suggest an alternative. If significant, schedule a call to discuss.

---

## Resources

### Internal
- See `CLAUDE.md` for coding standards
- See `TESTING_STRATEGY.md` for testing requirements
- See team playbook for architecture patterns

### External
- [Google's Code Review Guide](https://google.github.io/eng-practices/review/)
- [GitHub Code Review Best Practices](https://github.com/features/code-review)
- [Conventional Comments](https://conventionalcomments.org/)

---

**Last Updated**: [Date]
**Maintained By**: [Your name/team]
