To set up [PR Steward](</docs/en/pr-steward>), turn it on for your Claude organization and then for each repository. You need an [Owner role](</docs/en/server-managed-settings#access-control>). Once it’s on in a repository, PR Steward pushes commits to pull requests there to address review feedback, and attempts to fix failing checks and resolve merge conflicts. It starts by itself or when someone asks for it, as you choose for each repository.

## Prerequisites

Check that your organization [qualifies for PR Steward](</docs/en/pr-steward#availability>). In your Claude organization, which you manage at [claude.ai](<https://claude.ai/admin-settings>), you need:

  * An [Owner role](</docs/en/server-managed-settings#access-control>)
  * [Usage credits](<https://support.claude.com/en/articles/12429409-extra-usage-for-paid-claude-plans>), which pay for PR Steward’s work
  * The GitHub connector, turned on at [**Organization settings > Connectors**](<https://claude.ai/admin-settings/connectors>). With it on, people in your organization can [connect their GitHub accounts](</docs/en/web-quickstart#connect-github>) to Claude

On GitHub, you need this access, or someone who has it:

  * Owner of the GitHub organization, to install the [Claude GitHub App](<https://github.com/apps/claude>) and [link it to your Claude organization](</docs/en/admin-setup#connected-github-accounts>)
  * Admin of the repository, to add branch rules. A private repository also needs a [paid GitHub plan](<https://docs.github.com/en/get-started/learning-about-github/githubs-plans>)
  * Push access to the repository, from the GitHub account that you connect to Claude

## Require reviews with branch rules

Add these rules in GitHub before you turn on PR Steward.

1

Require an approval

Add a ruleset rule on the default branch that requires a pull request with at least one approval.

2

Require a new approval after a push

In that rule, dismiss stale approvals when new commits are pushed, or require approval of the most recent push.

3

Check the ruleset's bypass list

Keep the Claude GitHub App off the ruleset’s bypass list. On GitHub Enterprise Server, that’s [the app that your organization created](</docs/en/github-enterprise-server#admin-setup>). If PR Steward runs in a self-hosted environment, keep the runner’s git identity off it.

4

Protect other branches

Add rules to any other branch that PR Steward shouldn’t push to, and block force pushes where you don’t want them.

Where a [Claude Approvals policy lets Claude approve](</docs/en/approvals-github-rules#merges-without-human-review>), Claude’s review can count as the approval in step 1. An approval from a session in a self-hosted environment can count as well.

## Turn on PR Steward and add repositories

Start on [**Organization settings > Claude Ship**](<https://claude.ai/admin-settings/claude-ship>). The **Repositories** table on that page lists each repository with its **Steward** setting:

Adding a repository can start [Code Review](</docs/en/code-review-setup>) there, which is billed.

  * **No repository is listed yet** : a dialog asks what Claude does on the repositories that you add, and **Code review** is selected by default. If you select **Steward** in the dialog, PR Steward turns on for the organization and those repositories before you’ve set a spend limit.
  * **Others are already listed** : no dialog opens, and the new one is set up for review at every push by default.

To change that, [set when reviews run](</docs/en/code-review-setup#set-when-reviews-run>) or [turn off Code Review](</docs/en/code-review-setup#turn-off-code-review-or-remove-a-repository>) for the repository.

1

Add a repository

If the repository is already listed under **Repositories** , skip this step. Otherwise, click **Add** , connect your GitHub account if asked, and select the repository. If a dialog then asks what Claude does on it, click **Not now** , which keeps the repository listed.

2

Set which authors PR Steward works for

Under the **Steward** switch, use **Runs for** to set whose pull requests PR Steward works on. Select **All eligible authors** , or select **Listed users only** to pilot with a few people, and enter their GitHub usernames.On GitHub Enterprise Server, select **All eligible authors** , because PR Steward doesn’t start there with a list.

3

Turn on PR Steward for the organization

Click the **Steward** switch, then click **Turn on**.

4

Set PR Steward's monthly limit

Go to [**Organization settings > Usage**](<https://claude.ai/admin-settings/usage>). Under **Services** , set the limit in the **PR Steward** row. PR Steward has no spend limit of its own until you set one.

5

Turn on PR Steward for the repository

On the **Claude Ship** page, click **Edit** beside the repository. Set **Steward** to **Manual (@claude steward)**. Click **Change** beside **Steward spend cap** and enter the cap, in US dollars. See how the cap works.

6

Test PR Steward

Open a pull request from an account that has write access and that **Runs for** covers. Comment `@claude steward`. The `claude-pr-steward-watching` label and a comment headed **Claude PR Steward** appear.

If they don’t appear, see [Troubleshoot PR Steward](</docs/en/pr-steward-troubleshooting>).

## Roll out PR Steward to more pull requests

When PR Steward’s fixes match what your reviewers would do, set the repository to **On**. For each repository that you add later, require reviews there first. Then repeat these steps from Turn on PR Steward and add repositories: add the repository, turn on PR Steward for it, and test PR Steward. PR Steward can be on in up to 256 repositories.

### Choose when PR Steward starts in each repository

On the **Claude Ship** page, click **Edit** beside a repository and set **Steward** :

Option| When PR Steward starts
---|---
**Manual (@claude steward)**|  When a person with write access comments `@claude steward` or adds the `claude-pr-steward-watching` label
**On**|  When a pull request that [PR Steward doesn’t skip](</docs/en/pr-steward#when-pr-steward-starts>) is opened, reopened, or marked ready for review. Also at the next push to an open one that it hasn’t started on before
**On (including drafts)**|  The same as **On** , and on draft pull requests
**Off**|  PR Steward doesn’t start in the repository

In a **Manual** repository, a comment or the label can start PR Steward on [a draft](</docs/en/pr-steward-pull-requests#choose-what-pr-steward-works-on>). It doesn’t start PR Steward on the other pull requests that [PR Steward skips](</docs/en/pr-steward#when-pr-steward-starts>). PR Steward also starts there on the pull requests of a developer who selects [**Act on its own**](</docs/en/pr-steward-pull-requests#turn-off-or-limit-pr-steward-on-all-your-pull-requests>).

### Limit which authors PR Steward works for

To skip an author, add their GitHub username to **Excluded users** , under the **Steward** switch.

## Control what PR Steward spends

Billing [continues while usage credits are turned off](</docs/en/claude-ship#how-each-claude-ship-agent-is-billed>).

### See what PR Steward spent

To see the average for each merged pull request, open a repository’s **Edit** dialog. For your organization’s total over the last 30 days, go to [claude.ai/analytics/pr-steward](<https://claude.ai/analytics/pr-steward>).

### Set PR Steward’s spend limits

Change the monthly limit in [**Organization settings > Usage**](<https://claude.ai/admin-settings/usage>), under **Services** , in the **PR Steward** row. The row appears after you first turn on PR Steward. Change the spend cap in the repository’s **Edit** dialog. When PR Steward reaches a limit, look for its comment on the pull request:

  * **Its monthly limit, or your organization’s usage-credit limit** : PR Steward pauses. It picks up again at the next push or comment once usage credits can pay again
  * **The spend cap** : PR Steward stops on that pull request. Spend can pass the cap before it stops. A person with write access can start it again, with the full cap. When PR Steward works on a pull request for more than about a week, it can start a new [cloud session](</docs/en/claude-code-on-the-web>), and the full cap then applies again

With no usage credits left to spend, PR Steward doesn’t start, and the **Claude Ship** page shows **Steward cannot start on pull requests**. Add usage credits or raise the limit on the **Usage** page.

## Set up PR Steward’s build environment

Choose an environment for PR Steward when it needs more to build and test your code.

### Choose the environment PR Steward runs in

To add a setup script, environment variables, or different network access, use an [organization-shared environment](</docs/en/cloud-environments#organization-shared-environments>). On the **Claude Ship** page, select a **Default environment** under **Where it runs**. To override it for one repository, click **Change** beside **Environment** in the **Edit** dialog. With neither set, PR Steward can use your organization’s [default environment](</docs/en/cloud-environments#the-default-environment>). Without one, it runs in an Anthropic-hosted environment with no setup script and no environment variables.

### Run PR Steward in a self-hosted environment

For the environment that PR Steward runs in, you can select a [self-hosted environment](</docs/en/self-hosted-environments>). The [limits on approvals and merges](</docs/en/pr-steward-security#limits-on-approvals-and-merges>) are described for Anthropic-hosted sessions only. On a runner without [Anthropic-managed git](</docs/en/self-hosted-environments-deploy#use-the-anthropic-git-proxy>), PR Steward pushes with the runner’s own git credentials.

In a self-hosted environment, Claude can reach GitHub directly with [any GitHub credential that a session can read](</docs/en/self-hosted-environments-deploy#harden-your-deployment>). Anthropic’s service can’t refuse an approval that’s made that way. GitHub can count it toward the approvals that you require.

In a self-hosted environment, PR Steward doesn’t load a `CLAUDE.md` or rules file from the runner or from the runner’s checkout of the pull request. It doesn’t load a [managed `CLAUDE.md`](</docs/en/memory#deploy-organization-wide-claude-md>). Put what PR Steward should follow [on the repository’s default branch](</docs/en/pr-steward-pull-requests#save-pr-steward-instructions-for-everyone-in-a-repository>).

## Turn off PR Steward

When you turn off PR Steward, new starts stop. It keeps working for a time on pull requests that already have the `claude-pr-steward-watching` label. When you turn it off for one author, that time can be about a week. To stop PR Steward there as well, first remove the label from the pull requests that the change covers. Then turn off PR Steward on the **Claude Ship** page:

To turn off PR Steward for| Then
---|---
The organization| Click the **Steward** switch
One repository| Click **Edit** beside the repository and set **Steward** to **Off**
One author| Add their GitHub username to **Excluded users**

If you turned it off first, remove the labels afterward to stop PR Steward, unless your GitHub organization is linked to more than one Claude organization.

## Next steps

  * [Work with PR Steward](</docs/en/pr-steward-pull-requests>)
  * [What PR Steward can access](</docs/en/pr-steward-security>)
