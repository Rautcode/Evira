"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { FileCode2, MoreVertical, Plus, Search, Edit2, Copy, Trash2, Tag, UploadCloud, Save } from 'lucide-react';
import { getTemplates, createTemplate, deleteTemplate } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/context/auth-context';

export default function TemplatesPage() {
  const { isAtLeast } = useAuth();
  const canEdit = isAtLeast('engineer');
  const [searchTerm, setSearchTerm] = React.useState('');
  const [templates, setTemplates] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [editingTemplate, setEditingTemplate] = React.useState<any>(null);
  const [saving, setSaving] = React.useState(false);
  const { toast } = useToast();

  const fetchAll = () => {
    setLoading(true);
    getTemplates()
      .then(res => setTemplates(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  React.useEffect(() => {
    fetchAll();
  }, []);

  const handleCreateNew = () => {
    setEditingTemplate({
      id: '',
      name: '',
      category: 'General',
      description: '',
      content: { body: '<!-- Enter Jinja2 HTML here -->' }
    });
    setIsModalOpen(true);
  };

  const handleEdit = (tmpl: any) => {
    setEditingTemplate(tmpl);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteTemplate(id);
      toast({ title: 'Deleted', description: 'Template removed.' });
      fetchAll();
    } catch (e) {
      toast({ title: 'Error', description: 'Failed to delete.', variant: 'destructive' });
    }
  };

  const handleSave = async () => {
    if (!editingTemplate.id) return;
    setSaving(true);
    try {
      await createTemplate(editingTemplate);
      toast({ title: 'Saved', description: 'Template successfully saved.' });
      setIsModalOpen(false);
      fetchAll();
    } catch (e) {
      toast({ title: 'Error', description: 'Failed to save template.', variant: 'destructive' });
    } finally {
      setSaving(false);
    }
  };

  const filteredTemplates = templates.filter(t => 
    t.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    t.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto py-8 animate-fade-in text-slate-900 dark:text-slate-100">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Template Designer</h1>
          <p className="text-slate-500 dark:text-slate-400">Manage and upload your SCADA report templates.</p>
        </div>
        {canEdit && (
          <div className="flex gap-3">
            <Button variant="outline" className="rounded-xl border-slate-300 dark:border-slate-700 bg-white/50 dark:bg-slate-900/50 hover:bg-slate-100 dark:hover:bg-slate-800">
              <UploadCloud className="mr-2 h-4 w-4 text-blue-600 dark:text-blue-400" />
              Upload Template
            </Button>
            <Button onClick={handleCreateNew} className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/20">
              <Plus className="mr-2 h-4 w-4" />
              Create New
            </Button>
          </div>
        )}
      </div>

      <Card className="glass-card-premium border-slate-200/50 dark:border-slate-800/40 shadow-xl">
        <CardHeader className="border-b border-slate-100 dark:border-slate-800/50 pb-4 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg">Available Templates</CardTitle>
            <CardDescription>You have {templates.length} templates configured.</CardDescription>
          </div>
          <div className="relative w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input 
              placeholder="Search by name or tag..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 rounded-xl bg-slate-50/50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800"
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-slate-50/50 dark:bg-slate-900/20">
              <TableRow className="border-b border-slate-100 dark:border-slate-800/50 hover:bg-transparent">
                <TableHead className="w-[300px]">Template Name</TableHead>
                <TableHead>Format</TableHead>
                <TableHead>Tags</TableHead>
                <TableHead>Last Modified</TableHead>
                <TableHead>Size</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center text-slate-500">
                    Loading templates...
                  </TableCell>
                </TableRow>
              ) : filteredTemplates.length > 0 ? (
                filteredTemplates.map((template) => (
                  <TableRow key={template.id} className="border-b border-slate-50 dark:border-slate-800/30 hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400">
                          <FileCode2 className="h-4 w-4" />
                        </div>
                        {template.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-xs font-bold px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                        {template.category || 'General'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1.5 flex-wrap">
                        <span className="inline-flex items-center gap-1 text-[10px] uppercase font-bold tracking-wider text-slate-500 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 px-2 py-0.5 rounded-full">
                          <Tag className="h-2.5 w-2.5" /> HTML
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">{template.description || 'N/A'}</TableCell>
                    <TableCell className="text-slate-500 text-sm">--</TableCell>
                    <TableCell className="text-right">
                      {canEdit ? (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="rounded-full hover:bg-slate-100 dark:hover:bg-slate-800">
                              <MoreVertical className="h-4 w-4 text-slate-500" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-40 rounded-xl border-slate-200 dark:border-slate-800">
                            <DropdownMenuItem onClick={() => handleEdit(template)} className="cursor-pointer text-xs font-medium">
                              <Edit2 className="mr-2 h-3.5 w-3.5 text-blue-500" /> Edit Design
                            </DropdownMenuItem>
                            <DropdownMenuItem className="cursor-pointer text-xs font-medium">
                              <Copy className="mr-2 h-3.5 w-3.5 text-slate-500" /> Duplicate
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleDelete(template.id)} className="cursor-pointer text-xs font-medium text-red-600 dark:text-red-400 focus:text-red-600 dark:focus:text-red-400">
                              <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      ) : (
                        <span className="text-xs text-muted-foreground">View only</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center text-slate-500">
                    No templates found matching "{searchTerm}".
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      {/* Template Editor Dialog */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingTemplate?.id ? 'Edit Template' : 'Create New Template'}</DialogTitle>
            <DialogDescription>Modify the Jinja2 HTML layout and settings.</DialogDescription>
          </DialogHeader>
          {editingTemplate && (
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Template ID</Label>
                  <Input 
                    value={editingTemplate.id} 
                    onChange={e => setEditingTemplate({...editingTemplate, id: e.target.value})} 
                    placeholder="e.g. daily_summary"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Display Name</Label>
                  <Input 
                    value={editingTemplate.name} 
                    onChange={e => setEditingTemplate({...editingTemplate, name: e.target.value})} 
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input 
                  value={editingTemplate.description} 
                  onChange={e => setEditingTemplate({...editingTemplate, description: e.target.value})} 
                />
              </div>
              <div className="space-y-2">
                <Label>Jinja2 HTML Content</Label>
                <Textarea 
                  className="font-mono text-xs min-h-[300px] bg-slate-950 text-slate-50"
                  value={editingTemplate.content?.body || ''} 
                  onChange={e => setEditingTemplate({
                    ...editingTemplate, 
                    content: { ...editingTemplate.content, body: e.target.value }
                  })} 
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : <><Save className="w-4 h-4 mr-2"/> Save Template</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
