/**
 * Tool handler for creating a new bookshelf in Bookstack
 */
export async function handleCreateBookshelf(server, args) {
    try {
        // Validate arguments
        if (!args.name) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Bookshelf name is required" }, null, 2),
                }],
                isError: true
            };
        }

        // Get environment variables
        // Use the provided credentials directly
        const baseUrl = "https://knowledge.oculair.ca";
        const tokenId = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT";
        const tokenSecret = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE";

        console.log(`Using Bookstack API at ${baseUrl} to create bookshelf "${args.name}"`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        // Prepare payload
        const payload = {
            name: args.name
        };
        
        if (args.description) {
            payload.description = args.description;
        }
        
        if (args.books) {
            payload.books = args.books;
        }
        
        if (args.tags) {
            payload.tags = args.tags;
        }

        try {
            // Set up timeout with AbortController
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds timeout
            
            // Make the API request
            const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/shelves`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            
            // Clear the timeout
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify(data, null, 2),
                }],
            };
        } catch (error) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ 
                        error: `Network or HTTP error - ${error.message}` 
                    }, null, 2),
                }],
                isError: true
            };
        }
    } catch (error) {
        return server.createErrorResponse(error);
    }
}

/**
 * Tool definition for create_bookshelf
 */
export const createBookshelfToolDefinition = {
    name: 'create_bookshelf',
    description: 'Creates a new bookshelf in Bookstack',
    inputSchema: {
        type: 'object',
        properties: {
            name: {
                type: 'string',
                description: 'The name of the bookshelf',
            },
            description: {
                type: 'string',
                description: 'A description of the bookshelf',
            },
            books: {
                type: 'array',
                items: {
                    type: 'number'
                },
                description: 'A list of book IDs to include in the shelf',
            },
            tags: {
                type: 'array',
                items: {
                    type: 'object'
                },
                description: 'A list of tag objects (each with "name" and "value")',
            },
        },
        required: ['name'],
    },
};