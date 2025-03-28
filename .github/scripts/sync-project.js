const yaml = require('js-yaml');
const fs = require('fs');
const path = require('path');
const { marked } = require('marked');

const GITHUB_API_URL = 'https://api.github.com/graphql';

async function graphqlRequest(query, variables = {}) {
  const response = await fetch(GITHUB_API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.GH_PAT}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      variables,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  if (data.errors) {
    throw new Error(`GraphQL error: ${JSON.stringify(data.errors)}`);
  }

  return data.data;
}

async function getProjectItems(projectId) {
  const query = `
    query GetProjectItems($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              id
              content {
                ... on Issue {
                  id
                  title
                  number
                }
                ... on PullRequest {
                  id
                  title
                  number
                }
              }
            }
          }
        }
      }
    }
  `;
  const data = await graphqlRequest(query, { projectId });
  return data.node.items.nodes;
}

async function createProjectItem(projectId, title, body, labels = []) {
  // First create an issue
  const createIssueMutation = `
    mutation CreateIssue($input: CreateIssueInput!) {
      createIssue(input: $input) {
        issue {
          id
          number
        }
      }
    }
  `;

  const issueData = await graphqlRequest(createIssueMutation, {
    input: {
      repositoryId: process.env.REPOSITORY_ID,
      title,
      body,
      labels,
    },
  });

  // Then add it to the project
  const addToProjectMutation = `
    mutation AddProjectItem($input: AddProjectV2ItemByIdInput!) {
      addProjectV2ItemById(input: $input) {
        item {
          id
        }
      }
    }
  `;

  await graphqlRequest(addToProjectMutation, {
    input: {
      projectId,
      contentId: issueData.createIssue.issue.id,
    },
  });

  return issueData.createIssue.issue;
}

async function parseRoadmap() {
  const roadmapPath = path.join(process.cwd(), 'docs', 'Pepper_Roadmap', 'ROADMAP.md');
  const roadmapContent = fs.readFileSync(roadmapPath, 'utf8');
  
  // Parse the roadmap content to extract tasks
  const tasks = [];
  const lines = roadmapContent.split('\n');
  let currentSection = '';
  
  for (const line of lines) {
    if (line.startsWith('## ')) {
      currentSection = line.replace('## ', '').trim();
    } else if (line.startsWith('- [ ] ')) {
      tasks.push({
        title: line.replace('- [ ] ', '').trim(),
        section: currentSection,
      });
    }
  }
  
  return tasks;
}

async function syncProjectBoard() {
  try {
    const projectId = process.env.PROJECT_ID;
    if (!projectId) {
      throw new Error('PROJECT_ID environment variable is required');
    }

    // Get existing project items
    const existingItems = await getProjectItems(projectId);
    const existingTitles = new Set(
      existingItems.map(item => item.content.title)
    );

    // Parse roadmap tasks
    const tasks = await parseRoadmap();

    // Create new items for tasks that don't exist
    for (const task of tasks) {
      if (!existingTitles.has(task.title)) {
        const body = `## ${task.section}\n\n${task.title}`;
        await createProjectItem(projectId, task.title, body, ['roadmap']);
        console.log(`Created task: ${task.title}`);
      }
    }

    console.log('Project board sync completed successfully');
  } catch (error) {
    console.error('Error syncing project board:', error);
    process.exit(1);
  }
}

// Run the sync
syncProjectBoard(); 