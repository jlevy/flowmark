# Research Brief: Modern TypeScript CLI Architecture Patterns

**Last Updated**: 2025-12-30

**Status**: Complete

**Related**:

- [CLI Tool Development Rules](../../agent-rules/typescript-cli-tool-rules.md) —
  Actionable rules for CLI development

- [Modern TypeScript Monorepo Package](research-modern-typescript-monorepo-package.md) —
  Build tooling, package structure, CI/CD

- [Commander.js Documentation](https://github.com/tj/commander.js)

- [picocolors Documentation](https://github.com/alexeyraspopov/picocolors)

- [@clack/prompts Documentation](https://github.com/bombshell-dev/clack)

* * *

## Executive Summary

This research brief documents proven architectural patterns for building maintainable
TypeScript CLI applications using Commander.js.
These patterns emerged from production CLI tools and address common challenges: code
duplication across commands, dual output modes (human-readable vs machine-parseable),
consistent error handling, and testability.

The recommended architecture uses a **Base Command pattern** with an **OutputManager**
for dual-mode output, **Handler + Command separation** for clean organization, and
**git-based versioning** for accurate version strings.

**Research Questions**:

1. How should CLI commands be structured to minimize code duplication?

2. What patterns support both human-readable and JSON output modes?

3. How should version information be derived for CLI tools?

4. What directory structure best organizes CLI code in a library/CLI hybrid package?

* * *

## Research Methodology

### Approach

Patterns were extracted from production TypeScript CLI tools, analyzed for common
solutions to recurring problems, and documented with complete implementation examples.

### Sources

- Production CLI implementations in TypeScript monorepos

- Commander.js best practices and documentation

- Unix philosophy for output handling (stdout vs stderr)

- npm versioning conventions and semver sorting requirements

* * *

## Research Findings

### 1. Directory Structure

**Status**: Recommended

**Details**:

Organize CLI code for maintainability with clear separation between commands, shared
utilities, and type definitions:

```
scripts/cli/
├── cli.ts                  # Main entry point, program setup
├── commands/               # Command implementations (one file per command group)
│   ├── my-feature.ts       # Command with subcommands
│   └── simple-cmd.ts       # Simple single command
├── lib/                    # Shared utilities and base classes
│   ├── baseCommand.ts      # Base class for handlers
│   ├── outputManager.ts    # Unified output handling
│   ├── commandContext.ts   # Global option management
│   ├── *Formatters.ts      # Domain-specific formatters
│   └── shared.ts           # General utilities
└── types/
    └── commandOptions.ts   # Named types for command options
```

**Assessment**: This structure scales well from small CLIs to large ones with many
commands.
The `lib/` directory prevents code duplication, while `types/` keeps TypeScript
interfaces organized.

* * *

### 2. Base Command Pattern

**Status**: Strongly Recommended

**Details**:

Use a base class to eliminate duplicate code across commands.
This pattern centralizes:

- Command context extraction

- Output management initialization

- Client/API connection handling

- Error handling with consistent formatting

- Dry-run checking

```ts
// lib/baseCommand.ts
export abstract class BaseCommand {
  protected ctx: CommandContext;
  protected output: OutputManager;
  private client?: HttpClient;

  constructor(command: Command, format: OutputFormat) {
    this.ctx = getCommandContext(command);
    this.output = new OutputManager({ format, ...this.ctx });
  }

  protected getClient(): HttpClient {
    if (!this.client) {
      this.client = new HttpClient(getApiUrl());
    }
    return this.client;
  }

  protected async execute<T>(
    action: () => Promise<T>,
    errorMessage: string
  ): Promise<T> {
    try {
      return await action();
    } catch (error) {
      this.output.error(errorMessage, error);
      process.exit(1);
    }
  }

  protected checkDryRun(message: string, details?: object): boolean {
    if (this.ctx.dryRun) {
      logDryRun(message, details);
      return true;
    }
    return false;
  }

  abstract run(options: any): Promise<void>;
}

// Usage in command handler:
class MyCommandHandler extends BaseCommand {
  async run(options: MyCommandOptions): Promise<void> {
    if (this.checkDryRun('Would perform action', options)) return;

    const client = this.getClient();
    const result = await this.execute(
      () => client.query(api.something, {}),
      'Failed to fetch data'
    );

    this.output.data(result, () => displayResult(result, this.ctx));
  }
}
```

**Assessment**: The Base Command pattern dramatically reduces boilerplate.
New commands inherit consistent behavior for error handling, dry-run support, and output
formatting.

* * *

### 3. Dual Output Mode (Text + JSON)

**Status**: Strongly Recommended

**Details**:

Support both human-readable and machine-parseable output through an OutputManager class
that handles format switching transparently:

```ts
// lib/outputManager.ts
export class OutputManager {
  private format: 'text' | 'json';
  private quiet: boolean;
  private verbose: boolean;

  // Structured data - always goes to stdout
  data<T>(data: T, textFormatter?: (data: T) => void): void {
    if (this.format === 'json') {
      console.log(JSON.stringify(data, null, 2));
    } else if (textFormatter) {
      textFormatter(data);
    }
  }

  // Status messages - text mode only, stdout
  success(message: string): void {
    if (this.format === 'text' && !this.quiet) {
      p.log.success(message);
    }
  }

  // Errors - always stderr, always shown
  error(message: string, err?: Error): void {
    if (this.format === 'json') {
      console.error(JSON.stringify({ error: message, details: err?.message }));
    } else {
      console.error(colors.error(`Error: ${message}`));
    }
  }

  // Spinner - returns no-op in JSON/quiet mode
  spinner(message: string): Spinner {
    if (this.format === 'text' && !this.quiet) {
      const s = p.spinner();
      s.start(message);
      return { message: (m) => s.message(m), stop: (m) => s.stop(m) };
    }
    return { message: () => {}, stop: () => {} };
  }
}
```

**Key principles**:

| Output Type | Destination | When Shown |
| --- | --- | --- |
| Data (results) | stdout | Always |
| Success messages | stdout | Text mode, not quiet |
| Errors | stderr | Always |
| Warnings | stderr | Always |
| Spinners/progress | stdout | Text mode, not quiet |

**Assessment**: This pattern enables Unix pipeline compatibility (`my-cli list --format
json | jq '.items[]'`) while providing rich interactive output for terminal users.

* * *

### 4. Handler + Command Structure

**Status**: Recommended

**Details**:

Separate command definitions from implementation for cleaner code organization:

```ts
// commands/my-feature.ts

// 1. Handler class (extends BaseCommand)
class MyFeatureListHandler extends BaseCommand {
  async run(options: MyFeatureListOptions): Promise<void> {
    // Implementation
  }
}

// 2. Subcommand definition
const listCommand = withColoredHelp(new Command('list'))
  .description('List resources')
  .option('--limit <number>', 'Maximum results', '20')
  .action(async (options, command) => {
    setupDebug(getCommandContext(command));
    const format = validateFormat(options.format);
    const handler = new MyFeatureListHandler(command, format);
    await handler.run(options);
  });

// 3. Main command export (aggregates subcommands)
export const myFeatureCommand = withColoredHelp(new Command('my-feature'))
  .description('Manage resources')
  .addCommand(listCommand)
  .addCommand(showCommand)
  .addCommand(createCommand);
```

**Assessment**: This separation keeps command registration concise while allowing
complex handler logic.
The handler class is testable in isolation.

* * *

### 5. Named Option Types

**Status**: Recommended

**Details**:

Use named interfaces for command options to get TypeScript type checking:

```ts
// types/commandOptions.ts
export interface MyFeatureListOptions {
  limit: string;
  status: string | null;
  verbose: boolean;
}

export interface MyFeatureCreateOptions {
  name: string;
  description: string | null;
}

// Usage:
class MyFeatureListHandler extends BaseCommand {
  async run(options: MyFeatureListOptions): Promise<void> {
    const limit = parseInt(options.limit, 10);
    // TypeScript knows exactly what options are available
  }
}
```

**Assessment**: Named option types catch typos at compile time and provide autocomplete
in editors. Worth the small overhead of maintaining interface definitions.

* * *

### 6. Formatter Pattern

**Status**: Recommended

**Details**:

Pair text and JSON formatters for each domain.
Text formatters handle human-readable display; JSON formatters structure data for
machine consumption:

```ts
// lib/myFeatureFormatters.ts

// Text formatter - for human-readable output
export function displayMyFeatureList(items: Item[], ctx: CommandContext): void {
  if (items.length === 0) {
    p.log.info('No items found');
    return;
  }

  const table = createStandardTable(['ID', 'Name', 'Status']);
  for (const item of items) {
    table.push([item.id, item.name, formatStatus(item.status)]);
  }
  p.log.message('\n' + table.toString());
}

// JSON formatter - structured data for machine consumption
export function formatMyFeatureListJson(items: Item[]): object {
  return {
    total: items.length,
    items: items.map(item => ({
      id: item.id,
      name: item.name,
      status: item.status,
    })),
  };
}

// Usage in handler:
this.output.data(
  formatMyFeatureListJson(items),  // JSON format
  () => displayMyFeatureList(items, this.ctx)  // Text format
);
```

**Assessment**: Separating formatters makes them reusable and testable.
The JSON formatter defines the contract for machine consumers.

* * *

### 7. Version Handling

**Status**: Recommended

**Details**:

CLI tools should display accurate version information via `--version`. Use the `VERSION`
constant injected at build time via dynamic git-based versioning.

For the complete versioning implementation (format, rationale, and `getGitVersion()`
function), see [Dynamic Git-Based Versioning](research-modern-typescript-monorepo-patterns.md#dynamic-git-based-versioning)
in the monorepo patterns doc.

**CLI integration**:

```ts
// Import the build-time injected VERSION constant
import { VERSION } from '../index.js';

const program = new Command()
  .name('my-cli')
  .version(VERSION, '--version', 'Show version number')
  // ...
```

**Key points**:

- Use the exported `VERSION` constant from your library entry point
- Commander.js reserves `-V` and `--version` by default
- Avoid `-v` alias for other options (conflicts with version in some setups)

**Assessment**: Centralizing version in the library (injected at build time) ensures
CLI and programmatic consumers see the same version.

* * *

### 8. Global Options

**Status**: Recommended

**Details**:

Define global options once at the program level, not on individual commands:

```ts
// cli.ts
const program = new Command()
  .name('my-cli')
  .version(getVersionInfo().version)
  .option('--dry-run', 'Show what would be done without making changes')
  .option('--verbose', 'Enable verbose output')
  .option('--quiet', 'Suppress non-essential output')
  .option('--format <format>', 'Output format: text or json', 'text');

// Access via getCommandContext() in any command:
export function getCommandContext(command: Command): CommandContext {
  const opts = command.optsWithGlobals();
  return {
    dryRun: opts.dryRun ?? false,
    verbose: opts.verbose ?? false,
    quiet: opts.quiet ?? false,
    format: opts.format ?? 'text',
  };
}
```

**Assessment**: Centralizing global options ensures consistency and prevents option name
conflicts across commands.

* * *

### 9. Avoid Single-Letter Option Aliases

**Status**: Recommended

**Details**:

Use full option names to prevent conflicts in large CLIs:

```ts
// GOOD: Full names only
program
  .option('--dry-run', 'Show what would be done')
  .option('--verbose', 'Enable verbose output')
  .option('--quiet', 'Suppress output')

// AVOID: Single-letter aliases
program
  .option('-d, --dry-run', 'Show what would be done')  // -d might conflict
  .option('-v, --verbose', 'Verbose output')           // -v used by --version
```

**Assessment**: Single-letter aliases seem convenient but cause conflicts as CLIs grow.
Full names are self-documenting and avoid collisions.

* * *

### 10. Show Help After Errors

**Status**: Recommended

**Details**:

Configure Commander.js to display help after usage errors.
This helps users understand what went wrong and how to correctly use the command:

```ts
// In program setup (affects all commands)
const program = new Command()
  .name('my-cli')
  .showHelpAfterError()  // Show full help after errors
  // ... other options

// Or with a custom hint message (more concise)
program.showHelpAfterError('(add --help for additional information)');
```

This provides a better user experience when required arguments are missing or options
are invalid:

```console
$ my-cli research
error: missing required argument 'input'

Usage: my-cli research [options] <input>

Fill a form using a web-search-enabled model

Options:
  --model <provider/model>  Model to use (required)
  -h, --help                display help for command
```

When configured on the root program, this behavior propagates to all subcommands
automatically.

**Assessment**: This small configuration change significantly improves user experience
when commands are misused.

* * *

### 11. Stdout/Stderr Separation

**Status**: Essential

**Details**:

Route output appropriately for Unix pipeline compatibility:

```ts
// Data/success → stdout (can be piped)
console.log(JSON.stringify(data));
this.output.success('Operation complete');

// Errors/warnings → stderr (visible even when piped)
console.error('Error: something failed');
this.output.warn('Deprecated option');

// This enables: my-cli list --format json | jq '.items[]'
```

**Assessment**: Proper stdout/stderr separation is fundamental to Unix philosophy and
enables CLI tools to be composed in pipelines.

* * *

### 12. Testing with Dry-Run

**Status**: Recommended

**Details**:

Design commands to be testable via `--dry-run`:

```ts
class MyCommandHandler extends BaseCommand {
  async run(options: Options): Promise<void> {
    // Check dry-run early and return
    if (this.checkDryRun('Would create resource', {
      name: options.name,
      config: options.config,
    })) {
      return;
    }

    // Actual implementation only runs if not dry-run
    await this.createResource(options);
  }
}

// Test script can verify all commands with:
// my-cli resource create --name test --dry-run
// my-cli resource delete --id res-123 --dry-run
```

**Assessment**: Dry-run support enables safe testing of destructive commands and helps
users verify what a command will do before executing it.

* * *

### 13. Preaction Hooks

**Status**: Situational

**Details**:

Use Commander.js hooks for cross-cutting concerns like codegen or logging setup:

```ts
program.hook('preAction', (thisCommand) => {
  const commandName = thisCommand.name();

  // Run codegen before commands that need it
  if (!['help', 'docs', 'version'].includes(commandName)) {
    runCodegenIfNeeded({ silent: true });
  }

  // Set up logging based on verbose flag
  if (thisCommand.optsWithGlobals().verbose) {
    process.env.DEBUG = 'true';
  }
});
```

**Assessment**: Preaction hooks are useful for setup that should run before any command
but shouldn’t be duplicated in each command handler.

* * *

### 14. Documentation Command

**Status**: Recommended

**Details**:

Add a `docs` command that shows comprehensive help for all commands:

```ts
const docsCommand = new Command('docs')
  .description('Show full documentation for all commands')
  .action(async () => {
    let output = '';
    output += formatMainHelp(program);

    for (const cmd of program.commands) {
      output += formatCommandHelp(cmd);
      for (const subcmd of cmd.commands) {
        output += formatCommandHelp(subcmd);
      }
    }

    // Use pager for long output
    await showInPager(output);
  });
```

**Assessment**: A docs command provides a single reference for all CLI functionality,
which is especially valuable for CLIs with many subcommands.

* * *

## Best Practices Summary

1. **Use Base Command pattern** to eliminate boilerplate across commands

2. **Support dual output modes** (text + JSON) through OutputManager

3. **Separate handlers from command definitions** for testability

4. **Use named option types** for TypeScript safety

5. **Pair text and JSON formatters** for each data domain

6. **Use build-time VERSION constant** from library (see [monorepo patterns](research-modern-typescript-monorepo-patterns.md#dynamic-git-based-versioning))

7. **Define global options at program level** only

8. **Avoid single-letter aliases** to prevent conflicts

9. **Show help after errors** for better UX

10. **Route output correctly**: data to stdout, errors to stderr

11. **Support --dry-run** for safe testing of destructive commands

12. **Add a docs command** for comprehensive CLI documentation

* * *

## References

### Documentation

- [Commander.js](https://github.com/tj/commander.js) — CLI framework

- [picocolors](https://github.com/alexeyraspopov/picocolors) — Terminal colors

- [@clack/prompts](https://github.com/bombshell-dev/clack) — Interactive prompts

- [cli-table3](https://github.com/cli-table/cli-table3) — Table formatting

### Related Documentation

- [CLI Tool Development Rules](../../agent-rules/typescript-cli-tool-rules.md) —
  Actionable rules for CLI development

- [Modern TypeScript Monorepo Package](research-modern-typescript-monorepo-package.md) —
  Build tooling, package exports, CI/CD
