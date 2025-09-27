import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockClient = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
};

class MockApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

vi.mock('../../bookstack/BookstackClient.js', () => ({
  BookstackClient: {
    getInstance: () => mockClient,
  },
  BookstackApiError: MockApiError,
}));

const { default: BookstackListBooksTool } = await import('../BookstackListBooksTool.js');
const { default: BookstackListBookshelvesTool } = await import('../BookstackListBookshelvesTool.js');
const { default: BookstackListPagesTool } = await import('../BookstackListPagesTool.js');
const { default: BookstackCreatePageTool } = await import('../BookstackCreatePageTool.js');
const { default: BookstackUpdateBookTool } = await import('../BookstackUpdateBookTool.js');
const { default: BookstackUpdatePageTool } = await import('../BookstackUpdatePageTool.js');
const { default: BookstackReadBookTool } = await import('../BookstackReadBookTool.js');
const { default: BookstackReadPageTool } = await import('../BookstackReadPageTool.js');
const { default: BookstackDeleteBookTool } = await import('../BookstackDeleteBookTool.js');
const { default: BookstackSearchTool } = await import('../BookstackSearchTool.js');

const request = (args: Record<string, unknown>) => ({
  params: {
    arguments: args,
  },
});

beforeEach(() => {
  mockClient.get.mockReset();
  mockClient.post.mockReset();
  mockClient.put.mockReset();
  mockClient.delete.mockReset();
});

describe('Bookstack list tools', () => {
  it('returns paginated books', async () => {
    mockClient.get.mockResolvedValue({
      data: [{ id: 1, slug: 'sample', name: 'Sample Book' }],
      total: 1,
    });

    const tool = new BookstackListBooksTool();
    const response = await tool.toolCall(request({ count: 1 })) as { content: [{ type: string; text: string }] };

    expect(mockClient.get).toHaveBeenCalledWith('/api/books', { query: { offset: 0, count: 1 } });
    expect(response.content[0].type).toBe('text');
    const body = JSON.parse(response.content[0].text);
    expect(body.data[0].name).toBe('Sample Book');
  });

  it('returns validation error for invalid count', async () => {
    const tool = new BookstackListBooksTool();
    const response = await tool.toolCall(request({ count: 0 })) as { content: [{ type: string; text: string }] };

    expect(response.content[0].type).toBe('error');
    expect(response.content[0].text).toContain('count');
    expect(mockClient.get).not.toHaveBeenCalled();
  });
});

describe('Bookstack list shelves/pages tools', () => {
  it('lists bookshelves with pagination', async () => {
    mockClient.get.mockResolvedValue({
      data: [{ id: 5, name: 'Shelf', slug: 'shelf' }],
      total: 1,
    });

    const tool = new BookstackListBookshelvesTool();
    const response = await tool.toolCall(request({ offset: 10, count: 5 })) as { content: [{ type: string; text: string }] };

    expect(mockClient.get).toHaveBeenCalledWith('/api/bookshelves', { query: { offset: 10, count: 5 } });
    const body = JSON.parse(response.content[0].text);
    expect(body.data[0].slug).toBe('shelf');
  });

  it('lists pages', async () => {
    mockClient.get.mockResolvedValue({
      data: [{ id: 21, name: 'Page', book_id: 1 }],
      total: 20,
    });

    const tool = new BookstackListPagesTool();
    await tool.toolCall(request({ count: 2 }));

    expect(mockClient.get).toHaveBeenCalledWith('/api/pages', { query: { offset: 0, count: 2 } });
  });
});

describe('Bookstack create page tool', () => {
  it('requires either book_id or chapter_id', async () => {
    const tool = new BookstackCreatePageTool();
    const response = await tool.toolCall(request({ name: 'Untitled' })) as { content: [{ type: string; text: string }] };

    expect(response.content[0].type).toBe('error');
    expect(response.content[0].text).toContain('Either book_id or chapter_id');
    expect(mockClient.post).not.toHaveBeenCalled();
  });

  it('rejects both markdown and html payloads', async () => {
    const tool = new BookstackCreatePageTool();
    const response = await tool.toolCall(
      request({ name: 'Dual', book_id: 12, markdown: '# hi', html: '<p>hi</p>' }),
    ) as { content: [{ type: string; text: string }] };

    expect(response.content[0].type).toBe('error');
    expect(response.content[0].text).toContain('either markdown or html');
    expect(mockClient.post).not.toHaveBeenCalled();
  });

  it('creates a page with markdown content', async () => {
    mockClient.post.mockResolvedValue({ id: 10, name: 'Created' });

    const tool = new BookstackCreatePageTool();
    const response = await tool.toolCall(
      request({ name: 'Created', book_id: 12, markdown: '# Test' }),
    ) as { content: [{ type: string; text: string }] };

    expect(mockClient.post).toHaveBeenCalledWith('/api/pages', {
      name: 'Created',
      book_id: 12,
      markdown: '# Test',
    }, {});
    expect(response.content[0].type).toBe('text');
    const body = JSON.parse(response.content[0].text);
    expect(body.id).toBe(10);
  });
});

describe('Bookstack update book tool', () => {
  it('requires at least one field to update', async () => {
    const tool = new BookstackUpdateBookTool();
    const response = await tool.toolCall(request({ id: 1 })) as { content: [{ type: string; text: string }] };

    expect(response.content[0].type).toBe('error');
    expect(response.content[0].text).toContain('Provide at least one field');
    expect(mockClient.put).not.toHaveBeenCalled();
  });

  it('updates book title', async () => {
    mockClient.put.mockResolvedValue({ id: 1, name: 'Updated' });

    const tool = new BookstackUpdateBookTool();
    const response = await tool.toolCall(request({ id: 1, name: 'Updated' })) as { content: [{ type: string; text: string }] };

    expect(mockClient.put).toHaveBeenCalledWith('/api/books/1', { name: 'Updated' }, {});
    expect(response.content[0].type).toBe('text');
  });
});

describe('Bookstack update page tool', () => {
  it('requires at least one field to update', async () => {
    const tool = new BookstackUpdatePageTool();
    const response = await tool.toolCall(request({ id: 42 })) as { content: [{ type: string; text: string }] };

    expect(response.content[0].type).toBe('error');
    expect(response.content[0].text).toContain('Provide at least one field');
    expect(mockClient.put).not.toHaveBeenCalled();
  });

  it('rejects simultaneous markdown and html updates', async () => {
    const tool = new BookstackUpdatePageTool();
    const response = await tool.toolCall(
      request({ id: 42, markdown: '# hi', html: '<p>hi</p>' }),
    ) as { content: [{ type: string; text: string }] };

    expect(response.content[0].type).toBe('error');
    expect(response.content[0].text).toContain('either markdown or html');
    expect(mockClient.put).not.toHaveBeenCalled();
  });

  it('updates page name', async () => {
    mockClient.put.mockResolvedValue({ id: 42, name: 'Renamed' });

    const tool = new BookstackUpdatePageTool();
    const response = await tool.toolCall(request({ id: 42, name: 'Renamed' })) as { content: [{ type: string; text: string }] };

    expect(mockClient.put).toHaveBeenCalledWith('/api/pages/42', { name: 'Renamed' }, {});
    expect(response.content[0].type).toBe('text');
  });
});

describe('Bookstack read tools', () => {
  it('reads a book by id', async () => {
    mockClient.get.mockResolvedValue({ id: 2, name: 'Graphiti' });

    const tool = new BookstackReadBookTool();
    const response = await tool.toolCall(request({ id: 2 })) as { content: [{ type: string; text: string }] };

    expect(mockClient.get).toHaveBeenCalledWith('/api/books/2', {});
    const body = JSON.parse(response.content[0].text);
    expect(body.name).toBe('Graphiti');
  });

  it('maps API error when reading page', async () => {
    mockClient.get.mockRejectedValue(new MockApiError('not found', 404, { message: 'missing' }));

    const tool = new BookstackReadPageTool();
    const response = await tool.toolCall(request({ id: 404 })) as { content: [{ type: string; text: string }] };

    expect(response.content[0].type).toBe('error');
    expect(response.content[0].text).toContain('404');
  });
});

describe('Bookstack delete tools', () => {
  it('returns success flag when deleting a book', async () => {
    mockClient.delete.mockResolvedValue({});

    const tool = new BookstackDeleteBookTool();
    const response = await tool.toolCall(request({ id: 5 })) as { content: [{ type: string; text: string }] };

    expect(mockClient.delete).toHaveBeenCalledWith('/api/books/5', {});
    const body = JSON.parse(response.content[0].text);
    expect(body.success).toBe(true);
  });
});

describe('Bookstack search tool', () => {
  it('normalizes search results', async () => {
    mockClient.get.mockResolvedValue({
      data: [
        {
          id: 1,
          name: 'Graphiti Guide',
          type: 'page',
          url: 'https://example.com/page',
          preview_html: { content: '<p>Graphiti summary for testing.</p>' },
          book: { id: 2, name: 'Graphiti' },
        },
      ],
      total: 1,
    });

    const tool = new BookstackSearchTool();
    const response = await tool.toolCall(request({ query: 'Graphiti', count: 1 })) as { content: [{ type: string; text: string }] };

    expect(mockClient.get).toHaveBeenCalledWith('/api/search', {
      query: { query: 'Graphiti', count: 1 },
    });

    const body = JSON.parse(response.content[0].text);
    expect(body.results).toHaveLength(1);
    expect(body.results[0].summary).toContain('Graphiti');
  });

  it('maps Bookstack API errors', async () => {
    mockClient.get.mockRejectedValue(new MockApiError('boom', 502, { message: 'bad gateway' }));

    const tool = new BookstackSearchTool();
    const response = await tool.toolCall(request({ query: 'Graphiti' })) as { content: [{ type: string; text: string }] };

    expect(response.content[0].type).toBe('error');
    expect(response.content[0].text).toContain('Bookstack API error');
    expect(response.content[0].text).toContain('502');
  });
});
