@description('Region for all resources')
param location string = resourceGroup().location

@description('Name prefix used for all resources')
param appName string = 'aether-station'

@description('Container image to deploy (push to ACR first)')
param image string

@secure()
@description('Azure OpenAI API key (optional; leave blank for offline demo)')
param azureOpenAiKey string = ''

@description('Azure OpenAI endpoint')
param azureOpenAiEndpoint string = ''

@description('Azure OpenAI deployment name')
param azureOpenAiDeployment string = 'gpt-4o-mini'

@description('Local retrieval backend when Foundry IQ is not configured')
param retrieverBackend string = 'bm25'

resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${appName}-law'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${appName}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: law.listKeys().primarySharedKey
      }
    }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8501
        transport: 'auto'
      }
      secrets: [
        {
          name: 'azure-openai-key'
          value: azureOpenAiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'aether-station'
          image: image
          resources: { cpu: json('0.5'), memory: '1.0Gi' }
          env: [
            { name: 'RETRIEVER_BACKEND', value: retrieverBackend }
            { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
            { name: 'AZURE_OPENAI_API_KEY', secretRef: 'azure-openai-key' }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 1 }
    }
  }
}

output appUrl string = 'https://${app.properties.configuration.ingress.fqdn}'
