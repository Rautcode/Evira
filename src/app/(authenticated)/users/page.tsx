"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Users, Plus, Pencil, UserX, ShieldCheck } from "lucide-react";
import { getUsers, createUser, updateUser, deactivateUser } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/context/auth-context";

type Role = "operator" | "engineer" | "admin";

interface User { id: number; username: string; role: Role; active: boolean; }

const ROLE_BADGE: Record<Role, string> = {
  admin:    "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300",
  engineer: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300",
  operator: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300",
};

const EMPTY_FORM = { username: "", password: "", role: "operator" as Role };

export default function UsersPage() {
  const { isAtLeast } = useAuth();
  const { toast } = useToast();

  const [users, setUsers] = React.useState<User[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [editingUser, setEditingUser] = React.useState<User | null>(null);
  const [form, setForm] = React.useState(EMPTY_FORM);
  const [saving, setSaving] = React.useState(false);

  if (!isAtLeast("admin")) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <ShieldCheck className="h-6 w-6 mr-2" />
        Admin access required.
      </div>
    );
  }

  const fetchUsers = () => {
    setLoading(true);
    getUsers()
      .then((r) => setUsers(r.data))
      .catch(() => toast({ title: "Failed to load users", variant: "destructive" }))
      .finally(() => setLoading(false));
  };

  React.useEffect(() => { fetchUsers(); }, []);

  const openCreate = () => {
    setEditingUser(null);
    setForm(EMPTY_FORM);
    setDialogOpen(true);
  };

  const openEdit = (u: User) => {
    setEditingUser(u);
    setForm({ username: u.username, password: "", role: u.role });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!form.username.trim()) {
      toast({ title: "Username required", variant: "destructive" }); return;
    }
    if (!editingUser && form.password.length < 6) {
      toast({ title: "Password must be at least 6 characters", variant: "destructive" }); return;
    }
    setSaving(true);
    try {
      if (editingUser) {
        await updateUser(editingUser.id, { role: form.role, active: true, password: form.password || undefined });
        toast({ title: "User updated" });
      } else {
        await createUser({ username: form.username.trim(), password: form.password, role: form.role });
        toast({ title: "User created" });
      }
      setDialogOpen(false);
      fetchUsers();
    } catch (e: any) {
      const msg = e?.response?.data?.detail || "Failed to save user";
      toast({ title: "Error", description: msg, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (u: User) => {
    if (!confirm(`Deactivate "${u.username}"? They will no longer be able to log in.`)) return;
    try {
      await deactivateUser(u.id);
      toast({ title: "User deactivated" });
      fetchUsers();
    } catch {
      toast({ title: "Failed to deactivate", variant: "destructive" });
    }
  };

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-black tracking-tight flex items-center gap-2">
            <Users className="h-8 w-8 text-primary" /> User Management
          </h1>
          <p className="text-muted-foreground mt-1">Create accounts and assign roles. Operators can view data; Engineers can configure; Admins manage users.</p>
        </div>
        <Button onClick={openCreate} className="bg-blue-600 hover:bg-blue-700 text-white">
          <Plus className="h-4 w-4 mr-2" /> Add User
        </Button>
      </div>

      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>{users.length} user{users.length !== 1 ? "s" : ""}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={4} className="text-center py-10 text-muted-foreground">Loading…</TableCell></TableRow>
              ) : users.length === 0 ? (
                <TableRow><TableCell colSpan={4} className="text-center py-10 text-muted-foreground">No users found.</TableCell></TableRow>
              ) : users.map((u) => (
                <TableRow key={u.id} className={!u.active ? "opacity-50" : ""}>
                  <TableCell className="font-medium">{u.username}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={ROLE_BADGE[u.role] ?? ""}>
                      {u.role}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={u.active ? "default" : "secondary"}>
                      {u.active ? "Active" : "Inactive"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button variant="ghost" size="sm" onClick={() => openEdit(u)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    {u.active && (
                      <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive" onClick={() => handleDeactivate(u)}>
                        <UserX className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{editingUser ? "Edit User" : "New User"}</DialogTitle>
            <DialogDescription>
              {editingUser ? "Change role or reset password." : "Create a new application account."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1">
              <Label>Username</Label>
              <Input
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                disabled={!!editingUser}
                placeholder="e.g. john.smith"
              />
            </div>
            <div className="space-y-1">
              <Label>{editingUser ? "New password (leave blank to keep current)" : "Password"}</Label>
              <Input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder={editingUser ? "Leave blank to keep" : "Min 6 characters"}
              />
            </div>
            <div className="space-y-1">
              <Label>Role</Label>
              <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v as Role })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="operator">Operator — view & generate reports</SelectItem>
                  <SelectItem value="engineer">Engineer — configure system & templates</SelectItem>
                  <SelectItem value="admin">Admin — full access + user management</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving} className="bg-blue-600 hover:bg-blue-700 text-white">
              {saving ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
