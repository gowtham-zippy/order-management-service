// Infrastructure for the Order Management Service: Linux App Service plan,
// Python 3.12 web app with health check, and Application Insights.

@description('Base name for the web app. Must be globally unique.')
param webAppName string

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('App Service plan SKU.')
@allowed(['B1', 'B2', 'S1', 'P1v3'])
param sku string = 'B1'

var planName = '${webAppName}-plan'
var insightsName = '${webAppName}-insights'

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${webAppName}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: insightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  sku: {
    name: sku
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      appCommandLine: 'bash /home/site/wwwroot/startup.sh'
      alwaysOn: sku != 'B1'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      healthCheckPath: '/health'
      httpLoggingEnabled: true
      appSettings: [
        // The pipeline deploys a pre-built artifact; App Service must not rebuild it.
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'false' }
        { name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE', value: 'false' }
        { name: 'PYTHONPATH', value: '/home/site/wwwroot:/home/site/wwwroot/.python_packages_local' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: insights.properties.ConnectionString }
        { name: 'ApplicationInsightsAgent_EXTENSION_VERSION', value: '~3' }
      ]
    }
  }
}

output webAppName string = webApp.name
output defaultHostName string = webApp.properties.defaultHostName
output healthUrl string = 'https://${webApp.properties.defaultHostName}/health'
