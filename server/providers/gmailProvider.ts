import nodemailer from 'nodemailer';
import { EmailProvider, GmailConfig } from './index';

export class GmailProvider implements EmailProvider {
  name = 'Gmail';
  type = 'gmail' as const;
  private transporter: nodemailer.Transporter;
  private config: GmailConfig;

  constructor(config: GmailConfig) {
    this.config = config;
    this.transporter = nodemailer.createTransporter({
      service: 'gmail',
      auth: {
        user: config.email,
        pass: config.appPassword, // App Password, não senha normal
      },
    });
  }

  async send(job: {
    to: string;
    cc?: string[];
    bcc?: string[];
    subject: string;
    html?: string;
    text?: string;
  }): Promise<{ messageId: string; timestamp: string }> {
    try {
      const mailOptions = {
        from: this.config.email,
        to: job.to,
        cc: job.cc?.join(','),
        bcc: job.bcc?.join(','),
        subject: job.subject,
        html: job.html,
        text: job.text,
      };

      const result = await this.transporter.sendMail(mailOptions);
      
      return {
        messageId: result.messageId,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('[GmailProvider] Failed to send email:', error);
      throw error;
    }
  }

  async testConnection(): Promise<boolean> {
    try {
      await this.transporter.verify();
      return true;
    } catch (error) {
      console.error('[GmailProvider] Connection test failed:', error);
      return false;
    }
  }

  getConfig(): Record<string, any> {
    return {
      email: this.config.email,
      // Não retornar a senha por segurança
    };
  }
}
