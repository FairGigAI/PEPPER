const { Octokit } = require('@octokit/rest');
const yaml = require('js-yaml');
const fs = require('fs');
const path = require('path');

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

async function setupProjectBoard() {
  try {
    // Get the workspace path from GitHub Actions
    const workspacePath = process.env.GITHUB_WORKSPACE || process.cwd();
    
    // Read project board configuration
    const configPath = path.join(workspacePath, '.github/project-board.yml');
    console.log(`Reading configuration from: ${configPath}`);
    
    const config = yaml.load(
      fs.readFileSync(configPath, 'utf8')
    );

    // Create project board
    const { data: project } = await octokit.projects.createProject({
      owner: process.env.ORGANIZATION,
      name: config.name,
      body: config.description,
      private: true
    });

    console.log(`Created project board: ${project.name}`);

    // Create columns
    for (const column of config.columns) {
      const { data: columnData } = await octokit.projects.createColumn({
        project_id: project.id,
        name: column.name
      });

      console.log(`Created column: ${columnData.name}`);
    }

    // Create labels
    for (const label of config.labels) {
      await octokit.issues.createLabel({
        owner: process.env.ORGANIZATION,
        repo: process.env.REPOSITORY,
        name: label.name,
        color: label.color,
        description: label.description
      });

      console.log(`Created label: ${label.name}`);
    }

    // Create milestones
    for (const milestone of config.milestones) {
      await octokit.issues.createMilestone({
        owner: process.env.ORGANIZATION,
        repo: process.env.REPOSITORY,
        title: milestone.title,
        state: milestone.state,
        description: milestone.description,
        due_on: milestone.due_on
      });

      console.log(`Created milestone: ${milestone.title}`);
    }

    console.log('Project board setup completed successfully');
  } catch (error) {
    console.error('Error setting up project board:', error);
    console.error('Current working directory:', process.cwd());
    console.error('GitHub workspace:', process.env.GITHUB_WORKSPACE);
    process.exit(1);
  }
}

setupProjectBoard(); 