/**
 * Tool handler for updating a bookshelf in Bookstack
 */
export async function handleUpdateBookshelf(server, args) {
    try {
        // Validate arguments
        if (!args.id || typeof args.id !== 'number' || args.id <= 0) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Valid bookshelf ID is required" }, null, 2),
                }],
                isError: true
            };
        }
        
        if (!args.name && !args.description && !args.books && !args.tags) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "At least one field to update must be provided" }, null, 2),
                }],
                isError: true
            };
        }

        // Get environment variables
        // Use the provided credentials directly
        const baseUrl = "https://knowledge.oculair.ca";
        const tokenId = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT";
        const tokenSecret = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE";

        console.log(`Using Bookstack API at ${baseUrl} to update bookshelf with ID ${args.id}`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        try {
            // Get current bookshelf data first
            const controller1 = new AbortController();
            const timeoutId1 = setTimeout(() => controller1.abort(), 30000); // 30 seconds timeout
            
            const currentShelfResponse = await fetch(`${baseUrl.replace(/\/$/, '')}/api/shelves/${args.id}`, {
                method: 'GET',
                headers: headers,
                signal: controller1.signal
            });
            
            clearTimeout(timeoutId1);
            
            if (!currentShelfResponse.ok) {
                throw new Error(`Failed to retrieve current bookshelf data - HTTP error! Status: ${currentShelfResponse.status}`);
            }
            
            const currentData = await currentShelfResponse.json();
            
            // Prepare update payload with current values as defaults
            const payload = {
                name: args.name !== undefined ? args.name : currentData.name || "",
                description: args.description !== undefined ? args.description : currentData.description || ""
            };
            
            if (args.books !== undefined) {
                payload.books = args.books;
            }
            
            if (args.tags !== undefined) {
                payload.tags = args.tags;
            }
            
            // Make the update API request
            const controller2 = new AbortController();
            const timeoutId2 = setTimeout(() => controller2.abort(), 30000); // 30 seconds timeout
            
            const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/shelves/${args.id}`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify(payload),
                signal: controller2.signal
            });
            
            clearTimeout(timeoutId2);
            
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
 * Tool definition for update_bookshelf
 */
export const updateBookshelfToolDefinition = {
    name: 'update_bookshelf',
    description: 'Updates a bookshelf in Bookstack',
    inputSchema: {
        type: 'object',
        properties: {
            id: {
                type: 'number',
                description: 'The ID of the bookshelf to update',
            },
            name: {
                type: 'string',
                description: 'The new name of the bookshelf',
            },
            description: {
                type: 'string',
                description: 'A new description of the bookshelf',
            },
            books: {
                type: 'array',
                items: {
                    type: 'number'
                },
                description: 'A new list of book IDs to include in the shelf',
            },
            tags: {
                type: 'array',
                items: {
                    type: 'object',
                    properties: {
                        name: { type: 'string' },
                        value: { type: 'string' }
                    },
                    required: ['name', 'value'],
                    additionalProperties: false
                },
                description: 'A new list of tag objects (each with "name" and "value")',
            },
        },
        required: ['id'],
    },
};