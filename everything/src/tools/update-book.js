/**
 * Tool handler for updating a book in Bookstack
 */
export async function handleUpdateBook(server, args) {
    try {
        // Validate arguments
        if (!args.id || typeof args.id !== 'number' || args.id <= 0) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Valid book ID is required" }, null, 2),
                }],
                isError: true
            };
        }
        
        if (!args.name && !args.description && !args.tags && !args.image_id) {
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

        console.log(`Using Bookstack API at ${baseUrl} to update book with ID ${args.id}`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        try {
            // Get current book data first
            const controller1 = new AbortController();
            const timeoutId1 = setTimeout(() => controller1.abort(), 30000); // 30 seconds timeout
            
            const currentBookResponse = await fetch(`${baseUrl.replace(/\/$/, '')}/api/books/${args.id}`, {
                method: 'GET',
                headers: headers,
                signal: controller1.signal
            });
            
            clearTimeout(timeoutId1);
            
            if (!currentBookResponse.ok) {
                throw new Error(`Failed to retrieve current book data - HTTP error! Status: ${currentBookResponse.status}`);
            }
            
            const currentData = await currentBookResponse.json();
            
            // Prepare update payload with current values as defaults
            const payload = {
                name: args.name !== undefined ? args.name : currentData.name || "",
                description: args.description !== undefined ? args.description : currentData.description || ""
            };
            
            if (args.tags !== undefined) {
                payload.tags = args.tags;
            }
            
            if (args.image_id !== undefined) {
                payload.image_id = args.image_id;
            }
            
            // Make the update API request
            const controller2 = new AbortController();
            const timeoutId2 = setTimeout(() => controller2.abort(), 30000); // 30 seconds timeout
            
            const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/books/${args.id}`, {
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
 * Tool definition for update_book
 */
export const updateBookToolDefinition = {
    name: 'update_book',
    description: 'Updates a book in Bookstack',
    inputSchema: {
        type: 'object',
        properties: {
            id: {
                type: 'number',
                description: 'The ID of the book to update',
            },
            name: {
                type: 'string',
                description: 'The new name of the book',
            },
            description: {
                type: 'string',
                description: 'A new description of the book',
            },
            tags: {
                type: 'array',
                items: {
                    type: 'object'
                },
                description: 'A new list of tag objects (each with "name" and "value")',
            },
            image_id: {
                type: 'number',
                description: 'The ID of a new image to use as the cover',
            },
        },
        required: ['id'],
    },
};