// Stateless JWTs can't be "un-signed" on logout, so we track logged-out tokens
// in memory until they expire naturally. Good enough for a practice project;
// a real app would use Redis or a DB table so it survives a server restart.
const blacklist = new Set();

function blacklistToken(token) {
  blacklist.add(token);
}

function isBlacklisted(token) {
  return blacklist.has(token);
}

module.exports = { blacklistToken, isBlacklisted };
