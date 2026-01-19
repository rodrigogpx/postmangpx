export interface EmailProvider {
  name: string;
  type: 'gmail' | 'sendgrid' | 'aws-ses' | 'smtp';
  
  send(job: {
    to: string;
    cc?: string[];
    bcc?: string[];
    subject: string;
    html?: string;
    text?: string;
  }): Promise<{
    messageId: string;
    timestamp: string;
  }>;
  
  testConnection(): Promise<boolean>;
  
  getConfig(): Record<string, any>;
}

export interface GmailConfig {
  email: string;
  appPassword: string;
}

export interface SendGridConfig {
  apiKey: string;
  fromEmail: string;
}

export interface AwsSesConfig {
  accessKeyId: string;
  secretAccessKey: string;
  region: string;
  fromEmail: string;
}

export interface SmtpConfig {
  host: string;
  port: number;
  secure: boolean;
  auth: {
    user: string;
    pass: string;
  };
  fromEmail: string;
}

export type ProviderConfig = GmailConfig | SendGridConfig | AwsSesConfig | SmtpConfig;
