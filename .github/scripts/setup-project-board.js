const yaml = require('js-yaml');
const fs = require('fs');
const path = require('path');

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

async function getOrganizationId() {
  const query = `
    query {
      organization(login: "FairGigAI") {
        id
      }
    }
  `;
  const data = await graphqlRequest(query);
  return data.organization.id;
}

async function createProject(orgId, name, description) {
  const mutation = `
    mutation CreateProject($input: CreateProjectInput!) {
      createProject(input: $input) {
        project {
          id
          number
          title
          description
        }
      }
    }
  `;
  const variables = {
    input: {
      ownerId: orgId,
      title: name,
      description,
    },
  };
  const data = await graphqlRequest(mutation, variables);
  return data.createProject.project;
}

async function createField(projectId, field) {
  const mutation = `
    mutation CreateProjectField($input: CreateProjectFieldInput!) {
      createProjectField(input: $input) {
        projectField {
          id
          name
          type
          options {
            id
            name
            color
          }
        }
      }
    }
  `;

  const options = field.options.map(option => ({
    name: option.name,
    color: option.color,
  }));

  const variables = {
    input: {
      projectId,
      fieldType: field.type,
      name: field.name,
      options,
    },
  };

  const data = await graphqlRequest(mutation, variables);
  return data.createProjectField.projectField;
}

async function createView(projectId, view) {
  const mutation = `
    mutation CreateProjectView($input: CreateProjectViewInput!) {
      createProjectView(input: $input) {
        projectView {
          id
          name
          type
          layout {
            groupBy
            sortBy
          }
        }
      }
    }
  `;

  const variables = {
    input: {
      projectId,
      name: view.name,
      type: view.type,
      layout: view.layout,
    },
  };

  const data = await graphqlRequest(mutation, variables);
  return data.createProjectView.projectView;
}

async function setupProjectBoard() {
  try {
    console.log('Reading project board configuration...');
    const configPath = path.join(process.cwd(), '.github', 'project-board.yml');
    const config = yaml.load(fs.readFileSync(configPath, 'utf8'));

    console.log('Getting organization ID...');
    const orgId = await getOrganizationId();

    console.log('Creating project...');
    const project = await createProject(orgId, config.name, config.description);
    console.log(`Created project: ${project.title} (ID: ${project.id})`);

    console.log('Creating fields...');
    for (const field of config.fields) {
      const createdField = await createField(project.id, field);
      console.log(`Created field: ${createdField.name}`);
    }

    console.log('Creating views...');
    for (const view of config.views) {
      const createdView = await createView(project.id, view);
      console.log(`Created view: ${createdView.name}`);
    }

    console.log('Project board setup completed successfully!');
  } catch (error) {
    console.error('Error setting up project board:', error);
    process.exit(1);
  }
}

setupProjectBoard(); 