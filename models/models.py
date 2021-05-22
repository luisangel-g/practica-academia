from odoo import _, fields, models, api, exceptions

class make_student_invoices(models.TransientModel):
    _name = 'make.student.invoices'
    _description = 'Asistente para la generación de facturas'

    journal_id =fields.Many2one('account.journal', 'Diario', domain="[('type','=','sale')]")
    
    def make_invoices(self):
        active_ids = self._context['active_ids']
        category_obj = self.env['product.category']
        category_id = category_obj.search([('name','=','Factura colegiatura')])
        
        student_br = self.env['academia.student'].search(['id','=',active_ids])
        
        if category_id:
            product_obj = self.env['product.product']
            product_ids = product_obj.search([('categ_id', '=', category_id.id)])
            invoice_obj = self.env['account.invoice']
            
            partner_br = self.env['res.partner'].search([('student_id', '=', student_br.id)])
            partner_id = False
            if partner_br:
                partner_id = partner_br[0].id
            vals = {
                'partner_id' : partner_id,
                'account_id' : partner_br[0].property_account_receivable_id.id  
            }
        return True

class academia_materia_list(models.Model):
    _name = 'academia.materia.list'
    _description = 'academia materia list'

    grado_id = fields.Many2one('academia.grado', 'ID Referencia')
    materia_id = fields.Many2one('academia.materia', 'Materia', required=True)

class academia_grado(models.Model):
    _name = 'academia.grado'
    _description = 'Modelo de los grados que tiene la escuela'

    @api.depends('name', 'group')
    def calculate_name(self):
        complete_name = self.name + " / " + self.group
        self.complete_name = complete_name
        
    _rec_name = 'complete_name'

    name = fields.Selection([
        ('1', 'Primero'),
        ('2', 'Segundo'),
        ('3', 'Tercero'),
        ('4', 'Cuarto'),
        ('5', 'Quinto'),
        ('6', 'Sexto'),
    ], 'Grado', required=True)
    group = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C')
    ], 'Grupo', required=True)

    materia_ids = fields.One2many('academia.materia.list', 'grado_id', 'Materias')
    complete_name = fields.Char('Nombre completo', size=128, compute="calculate_name", store=True)
class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    company_type = fields.Selection(selection_add=[('is_school', 'Escuela'),('student_id', 'Estudiante')])
    student_id = fields.Many2one('academia.student','Estudiante')

class academia_student(models.Model):
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _name = "academia.student"
    _description = "Modelo para formación de estudiantes"
    
    @api.model
    def _get_school_default(self):
        school_id = self.env['res.partner'].search([('name', '=', 'Escuela comodin')])
        return school_id
    @api.depends('calificaciones_id')
    def calcular_promedio(self):
        acum = 0.0
        
        if len(self.calificaciones_id) > 0:
            for xcal in self.calificaciones_id:
                acum += xcal.calificacion
                if acum:
                    self.promedio = acum/len(self.calificaciones_id)
        else:
            self.promedio = 0.0

    name = fields.Char('Nombre', size=128, required=True, track_visibility='onchange')
    last_name = fields.Char('Apellido', size=128, copy=False)
    photo = fields.Binary('Fotografia')
    create_date = fields.Datetime('Fecha de creación', readonly=True)
    note = fields.Html('Comentarios')
    active = fields.Boolean('Activo')
    curp = fields.Char('curp', size=18, copy=False)
    age = fields.Integer('Edad')
    state = fields.Selection([
        ('draft', 'Documento borrador'),
        ('process', 'Proceso'),
        ('cancel', 'Expulsado'),
        ('done', 'Egresado')],'Estado', default="draft")
    
    ## relacionales
    partner_id = fields.Many2one('res.partner', 'Escuela', default=_get_school_default)
    country = fields.Many2one('res.country', 'Pais', related="partner_id.country_id")

    invoice_ids = fields.One2many('account.move.line', 'move_id', 'Facturas')

    calificaciones_id = fields.One2many(
        'academia.calificacion',
        'student_id',
        'Calificaciones'
    )

    grado_id = fields.Many2one('academia.grado', 'Grado')
    promedio = fields.Float('Promedio', digits=(3,2), compute="calcular_promedio")

    @api.onchange('grado_id')
    def onchange_grado(self):
        calificaciones_list = []
        for materia in self.grado_id.materia_ids:
            xval = (0,0,{
                'name': materia.materia_id.id,
                'calificacion': 5
            })
            calificaciones_list.append(xval)
        self.update({'calificaciones_id': calificaciones_list})

    #@api.model
    #def write(self, values):
    #    if 'curp' in values:
    #        values.update({
    #            'curp': values['curp'].upper()
    #        })
    #        return super(academia_student, self).write(values)
    #        
    @api.constrains('curp')
    def _check_curp(self):
        if len(self.curp) != 18:
            raise exceptions.ValidationError('La curp debe ser 18 digitos')
    
    @api.model
    def create(self, values):
        if values['name']:
            nombre = values['name']
            if self.env['academia.student'].search([('name', '=', self.name)]):
                values.update({
                    'name': values['name']+"(copy)"
                })
        res = super(academia_student, self).create(values)
        partner_obj = self.env['res.partner']
        vals_to_partner = {
            'name': res['name']+" "+res['last_name'],
            'company_type': "student_id",
        }
        print(vals_to_partner)
        partner = partner_obj.create(vals_to_partner)
        print('==> partner_id: ', partner)
        return res
    
    def unlink(self):
        partner_obj = self.env['res.partner']
        partners = partner_obj.search([('student', 'in', self.ids)])
        print("partners: ", partners)
        if partners:
            for partner in partners:
                partner.unlink()
        res = super(academia_student, self).unlink()
        return res
    _order = "name"
    _defaults = {
        "active": True
    }
    
    def confirm(self):
        self.state = 'process'
        return True
    
    def done(self):
        self.state = 'done'
        return True
    
    def cancel(self):
        self.state = 'cancel'
        return True
    
    def draft(self):
        self.state = 'draft'
        return True
    
    def generar(self):	
        return {
            'name': 'Generación de facturas',
            'res_model': 'make.student.invoices',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('modulo-practica.wizard_student_invoice').id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'key2': "client_action_multi",
            }