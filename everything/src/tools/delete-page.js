/**
 * Tool handler for deleting a page from Bookstack
 */
export async function handleDeletePage(server, args) {
    try {
        // Validate arguments
        if (!args.id || typeof args.id !== 'number' || args.id <= 0) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ error: "Valid page ID is required" }, null, 2),
                }],
                isError: true
            };
        }

        // Get environment variables
        // Use the provided credentials directly
        const baseUrl = "https://knowledge.oculair.ca";
        const tokenId = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT";
        const tokenSecret = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE";

        console.log(`Using Bookstack API at ${baseUrl} to delete page with ID ${args.id}`);

        // Set up request headers
        const headers = {
            'Authorization': `Token ${tokenId}:${tokenSecret}`,
            'Content-Type': 'application/json'
        };

        try {
            // Set up timeout with AbortController
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds timeout
            
            // Make the API request
            const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/pages/${args.id}`, {
                method: 'DELETE',
                headers: headers,
                signal: controller.signal
            });
            
            // Clear the timeout
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({
                        success: true,
                        message: `Page with ID ${args.id} deleted successfully`
                    }, null, 2),
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
 * Tool definition for delete_page
 */
export const deletePageToolDefinition = {
    name: 'delete_page',
    description: 'Deletes a page from Bookstack',
    inputSchema: {
        type: 'object',
        properties: {
            id: {
                type: 'number',
                description: 'The ID of the page to delete',
            },
        },
        required: ['id'],
    },
};