import { describe, it, expect, beforeEach, vi } from 'vitest';
import { appRouter } from './routers';
import { getDb } from './db';
import { emails } from '../drizzle/schema';

// Mock do banco de dados
vi.mock('./db', () => ({
  getDb: vi.fn(),
}));

// Mock do nanoid
vi.mock('nanoid', () => ({
  nanoid: vi.fn(() => 'test-email-id'),
}));

describe('emails.send', () => {
  let mockDb: any;
  let caller: any;

  beforeEach(() => {
    mockDb = {
      insert: vi.fn().mockReturnThis(),
      values: vi.fn().mockResolvedValue(undefined),
      select: vi.fn().mockReturnThis(),
      from: vi.fn().mockReturnThis(),
      where: vi.fn().mockReturnThis(),
      limit: vi.fn().mockResolvedValue([]),
    };

    vi.mocked(getDb).mockResolvedValue(mockDb);

    const mockCtx = {
      req: {
        headers: {
          authorization: 'Bearer pmgpx_test_12345678901234567890123456789012',
        },
      },
      res: {},
      user: null,
    };

    caller = appRouter.createCaller(mockCtx);
  });

  it('deve enviar um e-mail com sucesso', async () => {
    // Mock de template vazio
    mockDb.select.mockReturnValue({
      from: mockDb.from,
      where: mockDb.where,
      limit: mockDb.limit,
    });

    const result = await caller.emails.send({
      to: 'test@example.com',
      subject: 'Test Email',
      html: '<p>Hello World</p>',
    });

    expect(result.id).toBe('test-email-id');
    expect(result.status).toBe('pending');
    expect(mockDb.insert).toHaveBeenCalledWith(emails);
  });

  it('deve validar e-mail inválido', async () => {
    await expect(
      caller.emails.send({
        to: 'invalid-email',
        subject: 'Test',
        html: '<p>Hello</p>',
      })
    ).rejects.toThrow();
  });

  it('deve exigir conteúdo (html, text ou template)', async () => {
    await expect(
      caller.emails.send({
        to: 'test@example.com',
        subject: 'Test',
      })
    ).rejects.toThrow();
  });

  it('deve processar template com variáveis', async () => {
    // Mock de template
    mockDb.select.mockReturnValue({
      from: mockDb.from,
      where: mockDb.where,
      limit: mockDb.limit,
    });
    mockDb.limit.mockResolvedValue([
      {
        id: 'template-id',
        subject: 'Hello {{name}}',
        htmlContent: '<p>Welcome {{name}}!</p>',
        textContent: 'Welcome {{name}}!',
      },
    ]);

    const result = await caller.emails.send({
      to: 'test@example.com',
      template: 'template-id',
      variables: { name: 'John' },
    });

    expect(result.id).toBe('test-email-id');
    expect(mockDb.insert).toHaveBeenCalledWith(
      expect.objectContaining({
        subject: 'Hello John',
        htmlContent: '<p>Welcome John!</p>',
        textContent: 'Welcome John!',
      })
    );
  });
});
